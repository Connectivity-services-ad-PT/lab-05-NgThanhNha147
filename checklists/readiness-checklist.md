# Readiness Checklist - Lab 05

Checklist nay ghi lai trang thai stack Docker Compose sau khi chay kiem chung ngay 2026-06-09.

- [x] **Database ready:** `fit4110-db-lab05` dang `healthy`; `pg_isready -U lab05 -d iotdb` tra ve `accepting connections`.
- [x] **AI service ready:** `fit4110-ai-lab05` dang `healthy`; `GET http://localhost:9000/health` tra ve `200` va `POST /predict` pass trong Newman.
- [x] **API ready:** `fit4110-api-lab05` dang `healthy`; `GET /health` tra ve dependency `database=ok`, `ai=ok`; tao va doc readings thanh cong.
- [x] **Environment variables:** `.env.example` co `APP_PORT`, `AI_PORT`, `POSTGRES_*`, `AUTH_TOKEN`, `SERVICE_VERSION`; `.env` that bi ignore boi `.gitignore`.
- [x] **Network & Ports:** `team-internal` hoat dong trong Compose; `class-net` duoc tao voi dung ten; ports 8000, 9000 va 5432 duoc map ra host.
- [x] **Image tags:** local images da build voi tag `fit4110/iot-ingestion:v0.1.0-team-iot` va `fit4110/ai-service:v0.1.0-team-iot`. Registry push can Docker Hub/GHCR credentials nen chua thuc hien trong workspace nay.

Evidence:

- `reports/newman-lab05-compose.xml`
- `reports/newman-lab05-compose.html`
- `reports/compose-evidence.md`
