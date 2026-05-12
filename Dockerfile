FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt backend/pyproject.toml /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt && \
    pip install --no-cache-dir scrapling[fetchers]

COPY . /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
