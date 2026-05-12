FROM python:3.11-slim

RUN groupadd -r leadiq && useradd -r -g leadiq leadiq

WORKDIR /app

# Install backend dependencies first (uses uv for speed)
COPY backend/uv.lock ./backend/uv.lock
COPY backend/pyproject.toml ./backend/pyproject.toml
RUN pip install uv && uv sync --project backend --no-dev && \
    rm -rf /root/.cache

# Install actor-specific dependencies
COPY workers/internshala-actor/requirements.txt ./workers/internshala-actor/requirements.txt
RUN pip install -r workers/internshala-actor/requirements.txt && \
    rm -rf /root/.cache

# Copy the entire project (backend package + actor code)
COPY --chown=leadiq:leadiq backend/ ./backend/
COPY --chown=leadiq:leadiq workers/internshala-actor/main.py ./workers/internshala-actor/main.py

USER leadiq

CMD ["python", "-m", "workers.internshala-actor.main"]
