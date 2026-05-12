FROM python:3.11-slim

RUN groupadd -r leadiq && useradd -r -g leadiq leadiq

WORKDIR /app

# Install backend dependencies first (uses uv for speed)
COPY backend/uv.lock ./backend/uv.lock
COPY backend/pyproject.toml ./backend/pyproject.toml
RUN pip install uv && uv sync --project backend --no-dev && \
    rm -rf /root/.cache

# Install actor-specific dependencies
COPY workers/naukri-actor/requirements.txt ./workers/naukri-actor/requirements.txt
RUN pip install -r workers/naukri-actor/requirements.txt && \
    rm -rf /root/.cache

# Copy the entire project (backend package + actor code)
COPY --chown=leadiq:leadiq backend/ ./backend/
COPY --chown=leadiq:leadiq workers/naukri-actor/main.py ./workers/naukri-actor/main.py

USER leadiq

CMD ["python", "-m", "workers.naukri-actor.main"]
