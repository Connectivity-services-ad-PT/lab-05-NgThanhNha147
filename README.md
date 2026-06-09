# FIT4110 Lab 05 - Docker Compose Readiness

Repo nay dong goi mot stack Smart Campus mau de nguoi khac clone ve va chay lai duoc toan bo bang Docker Compose.

Stack gom:

- `api`: FastAPI IoT Ingestion API, port `8000`.
- `ai-service`: mock AI inference service, port `9000`.
- `db`: PostgreSQL 15, port `5432`.

API se:

- kiem tra DB va AI trong endpoint `/health`;
- goi `ai-service` qua hostname noi bo `http://ai-service:9000`;
- luu readings vao PostgreSQL;
- duoc test end-to-end bang Newman.

## Yeu cau

- Git.
- Docker Desktop hoac Docker Engine co Docker Compose v2.
- Node.js va npm de chay Newman/Spectral.

## Chay nhanh tu repo moi clone

```bash
git clone https://github.com/Connectivity-services-ad-PT/lab-05-NgThanhNha147.git
cd lab-05-NgThanhNha147
npm install
docker compose up -d --build
docker compose ps
npm run test:compose
```

Neu muon tuy bien port/token/password, tao `.env` tu file mau:

```bash
cp .env.example .env
```

Tren PowerShell:

```powershell
Copy-Item .env.example .env
```

Khong can tao `.env` neu chi muon chay voi gia tri mac dinh.

## Kiem tra readiness

```bash
curl http://localhost:8000/health
curl http://localhost:9000/health
docker exec fit4110-db-lab05 pg_isready -U lab05 -d iotdb
```

API `/health` can tra ve:

```json
{
  "status": "ok",
  "service": "iot-ingestion",
  "version": "v0.1.0-team-iot",
  "dependencies": {
    "database": "ok",
    "ai": "ok"
  }
}
```

## Newman report

Chay:

```bash
npm run test:compose
```

Report duoc tao tai:

```text
reports/newman-lab05-compose.xml
reports/newman-lab05-compose.html
```

Collection dang dung:

```text
postman/collections/FIT4110_lab05_iot_compose.postman_collection.json
```

Environment dang dung:

```text
postman/environments/FIT4110_lab05_local.postman_environment.json
```

## Lenh huu ich

```bash
docker compose logs -f
docker compose down
docker compose down -v
```

Neu may co `make`:

```bash
make install
make compose-up
make test-compose
make compose-down
```

## Cau truc repo

```text
.
|-- Dockerfile
|-- docker-compose.yml
|-- .dockerignore
|-- .env.example
|-- Makefile
|-- README.md
|-- RUN_COMPOSE.md
|-- requirements.txt
|-- contracts/
|   `-- iot-ingestion.openapi.yaml
|-- postman/
|   |-- collections/
|   |   `-- FIT4110_lab05_iot_compose.postman_collection.json
|   `-- environments/
|       `-- FIT4110_lab05_local.postman_environment.json
|-- reports/
|   |-- compose-evidence.md
|   |-- newman-lab05-compose.html
|   `-- newman-lab05-compose.xml
|-- checklists/
|   `-- readiness-checklist.md
`-- src/
    |-- ai_service/
    |   |-- Dockerfile
    |   `-- main.py
    `-- iot_app/
        |-- __init__.py
        `-- main.py
```

## Ghi chu

- `docker-compose.yml` co `build`, nen nguoi clone khong can pull image tu registry.
- `.env` bi ignore; chi commit `.env.example`.
- Image local duoc tag theo quy uoc:
  - `fit4110/iot-ingestion:v0.1.0-team-iot`
  - `fit4110/ai-service:v0.1.0-team-iot`
- Push image len Docker Hub/GHCR can credential rieng, khong nam trong repo.
