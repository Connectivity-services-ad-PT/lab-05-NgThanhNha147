# Lab 05 Compose Evidence

Captured on 2026-06-09.

## Container Readiness

```text
fit4110-ai-lab05    fit4110/ai-service:v0.1.0-team-iot      Up (healthy)   0.0.0.0:9000->9000/tcp
fit4110-api-lab05   fit4110/iot-ingestion:v0.1.0-team-iot   Up (healthy)   0.0.0.0:8000->8000/tcp
fit4110-db-lab05    postgres:15-alpine                      Up (healthy)   0.0.0.0:5432->5432/tcp
```

## Health Checks

API:

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

AI:

```json
{
  "status": "ok",
  "service": "ai-service",
  "version": "v0.1.0-team-iot"
}
```

Database:

```text
/var/run/postgresql:5432 - accepting connections
```

## Newman Result

```text
Collection: FIT4110 Lab05 IoT Compose
Requests: 8 executed, 0 failed
Assertions: 16 executed, 0 failed
Report XML: reports/newman-lab05-compose.xml
Report HTML: reports/newman-lab05-compose.html
```

## Image Tags

```text
fit4110/iot-ingestion:v0.1.0-team-iot
fit4110/ai-service:v0.1.0-team-iot
postgres:15-alpine
```

Registry push was not performed because no Docker Hub or GHCR credentials are available in this workspace.
