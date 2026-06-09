# Postman Collections

Collection Lab 05 hien co:

- `FIT4110_lab05_iot_compose.postman_collection.json`

Collection nay test stack Docker Compose end-to-end:

- API `/health` voi dependency `database=ok` va `ai=ok`.
- AI `/health` va `/predict`.
- Tao reading qua `POST /readings`.
- Doc latest/detail readings tu API.
- Negative tests cho missing token va validation error.

Chay bang:

```bash
npm run test:compose
```
