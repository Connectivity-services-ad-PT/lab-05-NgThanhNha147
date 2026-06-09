# RUN_COMPOSE.md - Lab 05

Tai lieu nay huong dan chay lai stack Docker Compose cua Lab 05 tren may sach.

## 1. Chuan bi

Can co:

- Docker Desktop hoac Docker Engine co Compose v2.
- Node.js va npm neu muon chay Newman/Spectral.

Neu muon tuy bien bien moi truong:

```bash
cp .env.example .env
```

Neu khong tao `.env`, Compose van dung gia tri mac dinh trong `docker-compose.yml`.

## 2. Cai dependency test

```bash
npm install
```

## 3. Build va chay stack

```bash
docker compose up -d --build
```

Stack gom 3 service:

- `fit4110-db-lab05`: PostgreSQL, port 5432.
- `fit4110-ai-lab05`: mock AI service, port 9000.
- `fit4110-api-lab05`: FastAPI IoT API, port 8000.

Xem trang thai:

```bash
docker compose ps
```

Xem log:

```bash
docker compose logs -f
```

## 4. Kiem tra readiness

```bash
curl http://localhost:8000/health
curl http://localhost:9000/health
docker exec fit4110-db-lab05 pg_isready -U lab05 -d iotdb
```

API `/health` phai tra ve `database=ok` va `ai=ok`.

## 5. Chay Newman

```bash
npm run test:compose
```

Report duoc sinh tai:

```text
reports/newman-lab05-compose.xml
reports/newman-lab05-compose.html
```

## 6. Dung stack

```bash
docker compose down
```

Neu muon xoa ca volume database:

```bash
docker compose down -v
```
