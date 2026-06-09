import os
from datetime import datetime, timezone
from enum import Enum
from http import HTTPStatus
from typing import Dict, List, Optional

import psycopg
import requests
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from psycopg.rows import dict_row

SERVICE_NAME = os.getenv("SERVICE_NAME", "iot-ingestion")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "0.5.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "local-dev-token")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "lab05")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "lab05pass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "iotdb")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:9000").rstrip("/")

app = FastAPI(
    title="FIT4110 Lab 05 - IoT Ingestion Service",
    version=SERVICE_VERSION,
    description=(
        "IoT Ingestion API for Lab 05 Docker Compose readiness. "
        "The API stores readings in PostgreSQL and calls the internal AI service."
    ),
)


class SensorMetric(str, Enum):
    temperature = "temperature"
    humidity = "humidity"
    motion = "motion"
    smoke = "smoke"


class SensorUnit(str, Enum):
    celsius = "celsius"
    percent = "percent"
    boolean = "boolean"
    ppm = "ppm"


class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int = Field(..., ge=400, le=599)
    detail: str
    instance: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    dependencies: Dict[str, str] = Field(default_factory=dict)


class SensorReadingCreate(BaseModel):
    device_id: str = Field(..., min_length=3, examples=["ESP32-LAB-A01"])
    metric: SensorMetric = Field(..., examples=["temperature"])
    value: float = Field(
        ...,
        ge=-40,
        le=80,
        description="Boundary range used in Lab 03/04: -40 to 80.",
        examples=[31.5],
    )
    unit: Optional[SensorUnit] = Field(default=None, examples=["celsius"])
    timestamp: str = Field(..., examples=["2026-05-13T08:30:00+07:00"])


class SensorReading(BaseModel):
    reading_id: str
    device_id: str
    metric: SensorMetric
    value: float
    unit: Optional[SensorUnit] = None
    timestamp: str
    created_at: str


class SensorReadingCreated(BaseModel):
    reading_id: str
    device_id: str
    metric: SensorMetric
    accepted: bool
    created_at: str


READINGS: List[Dict] = []


def database_dsn() -> str:
    return (
        f"host={POSTGRES_HOST} port={POSTGRES_PORT} dbname={POSTGRES_DB} "
        f"user={POSTGRES_USER} password={POSTGRES_PASSWORD}"
    )


def get_db_connection():
    return psycopg.connect(database_dsn(), autocommit=True)


def init_database() -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    reading_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    value DOUBLE PRECISION NOT NULL,
                    unit TEXT,
                    reading_timestamp TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    ai_objects TEXT NOT NULL DEFAULT '',
                    ai_confidence TEXT NOT NULL DEFAULT ''
                )
                """
            )


@app.on_event("startup")
def startup() -> None:
    init_database()


def build_problem(
    *,
    status_code: int,
    title: str,
    detail: str,
    instance: Optional[str] = None,
    problem_type: str = "about:blank",
) -> Dict:
    problem = {
        "type": problem_type,
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance:
        problem["instance"] = instance
    return problem


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        problem = exc.detail
    else:
        problem = build_problem(
            status_code=exc.status_code,
            title=reason_phrase(exc.status_code),
            detail=str(exc.detail),
            instance=str(request.url.path),
        )

    problem.setdefault("status", exc.status_code)
    problem.setdefault("title", reason_phrase(exc.status_code))
    problem.setdefault("type", "about:blank")
    problem.setdefault("detail", "Request failed")
    problem.setdefault("instance", str(request.url.path))

    return JSONResponse(
        status_code=exc.status_code,
        content=problem,
        media_type="application/problem+json",
        headers=getattr(exc, "headers", None),
    )


def reason_phrase(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "HTTP Error"


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(item) for item in first_error.get("loc", []))
    message = first_error.get("msg", "Request validation error")
    detail = f"{location}: {message}" if location else message

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_problem(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Validation error",
            detail=detail,
            instance=str(request.url.path),
            problem_type="https://smart-campus.local/problems/validation-error",
        ),
        media_type="application/problem+json",
    )


def verify_bearer_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=build_problem(
                status_code=status.HTTP_401_UNAUTHORIZED,
                title="Unauthorized",
                detail="Missing Authorization header",
                problem_type="https://smart-campus.local/problems/unauthorized",
            ),
        )

    expected = f"Bearer {AUTH_TOKEN}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=build_problem(
                status_code=status.HTTP_401_UNAUTHORIZED,
                title="Unauthorized",
                detail="Invalid bearer token",
                problem_type="https://smart-campus.local/problems/unauthorized",
            ),
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def next_reading_id() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"R-{today}-"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM sensor_readings WHERE reading_id LIKE %s",
                    (f"{prefix}%",),
                )
                count = cur.fetchone()[0]
        return f"{prefix}{count + 1:04d}"
    except psycopg.Error:
        return f"{prefix}{len(READINGS) + 1:04d}"


def check_database() -> str:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return "ok"
    except Exception as exc:
        return f"error: {exc.__class__.__name__}"


def check_ai_service() -> str:
    try:
        ai_response = requests.get(f"{AI_SERVICE_URL}/health", timeout=2)
        ai_response.raise_for_status()
        return "ok"
    except Exception as exc:
        return f"error: {exc.__class__.__name__}"


def call_ai_predict() -> Dict:
    ai_response = requests.post(f"{AI_SERVICE_URL}/predict", timeout=3)
    ai_response.raise_for_status()
    return ai_response.json()


def insert_reading(item: Dict, prediction: Dict) -> None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sensor_readings (
                    reading_id, device_id, metric, value, unit,
                    reading_timestamp, created_at, ai_objects, ai_confidence
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    item["reading_id"],
                    item["device_id"],
                    item["metric"],
                    item["value"],
                    item["unit"],
                    item["timestamp"],
                    item["created_at"],
                    ",".join(prediction.get("objects", [])),
                    ",".join(str(value) for value in prediction.get("confidence", [])),
                ),
            )


def fetch_readings(device_id: Optional[str], limit: int) -> List[Dict]:
    query = """
        SELECT reading_id, device_id, metric, value, unit,
               reading_timestamp AS timestamp, created_at
        FROM sensor_readings
    """
    params = []
    if device_id:
        query += " WHERE device_id = %s"
        params.append(device_id)
    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    with get_db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            rows = [dict(row) for row in cur.fetchall()]
    return list(reversed(rows))


def fetch_reading_by_id(reading_id: str) -> Optional[Dict]:
    with get_db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT reading_id, device_id, metric, value, unit,
                       reading_timestamp AS timestamp, created_at
                FROM sensor_readings
                WHERE reading_id = %s
                """,
                (reading_id,),
            )
            row = cur.fetchone()
    return dict(row) if row else None


@app.get("/health", response_model=HealthResponse)
def health(response: Response) -> HealthResponse:
    dependencies = {
        "database": check_database(),
        "ai": check_ai_service(),
    }
    is_ready = all(value == "ok" for value in dependencies.values())
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="ok" if is_ready else "degraded",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        dependencies=dependencies,
    )


@app.post(
    "/readings",
    response_model=SensorReadingCreated,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_bearer_token)],
    responses={
        401: {"model": ProblemDetails},
        422: {"model": ProblemDetails},
        503: {"model": ProblemDetails},
    },
)
def create_reading(payload: SensorReadingCreate, response: Response) -> SensorReadingCreated:
    if payload.metric == SensorMetric.temperature and payload.value >= 70:
        response.headers["X-Warning"] = "high-temperature"

    reading_id = next_reading_id()
    created_at = now_iso()

    item = {
        "reading_id": reading_id,
        "device_id": payload.device_id,
        "metric": payload.metric.value,
        "value": payload.value,
        "unit": payload.unit.value if payload.unit else None,
        "timestamp": payload.timestamp,
        "created_at": created_at,
    }

    try:
        prediction = call_ai_predict()
        insert_reading(item, prediction)
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=build_problem(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                title="AI service unavailable",
                detail=f"Could not call AI service: {exc.__class__.__name__}",
                problem_type="https://smart-campus.local/problems/ai-unavailable",
            ),
        ) from exc
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=build_problem(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                title="Database unavailable",
                detail=f"Could not persist reading: {exc.__class__.__name__}",
                problem_type="https://smart-campus.local/problems/database-unavailable",
            ),
        ) from exc

    READINGS.append(item)

    return SensorReadingCreated(
        reading_id=reading_id,
        device_id=payload.device_id,
        metric=payload.metric,
        accepted=True,
        created_at=created_at,
    )


@app.get("/readings/latest", dependencies=[Depends(verify_bearer_token)])
def latest_readings(
    device_id: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
) -> Dict[str, List[Dict]]:
    try:
        items = fetch_readings(device_id, limit)
    except psycopg.Error:
        items = READINGS
        if device_id:
            items = [item for item in items if item["device_id"] == device_id]
        items = items[-limit:]

    return {"items": items}


@app.get("/readings/{reading_id}", dependencies=[Depends(verify_bearer_token)])
def get_reading(reading_id: str) -> Dict:
    try:
        item = fetch_reading_by_id(reading_id)
        if item:
            return item
    except psycopg.Error:
        for item in READINGS:
            if item["reading_id"] == reading_id:
                return item

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=build_problem(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Not Found",
            detail=f"Reading {reading_id} does not exist",
            instance=f"/readings/{reading_id}",
            problem_type="https://smart-campus.local/problems/not-found",
        ),
    )
