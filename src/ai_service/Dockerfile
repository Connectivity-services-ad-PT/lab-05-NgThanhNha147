FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /service

RUN addgroup --system aigroup \
    && adduser --system --ingroup aigroup --home /service aiuser \
    && pip install --no-cache-dir fastapi==0.115.6 uvicorn[standard]==0.34.0 pydantic==2.10.4

COPY main.py .

RUN chown -R aiuser:aigroup /service

USER aiuser

EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9000/health', timeout=3).read()" || exit 1

CMD ["python", "main.py"]
