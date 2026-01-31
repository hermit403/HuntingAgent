# This is a Dockerfile for a CTF challenge, which is different from an actual production environment
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONPYTHONDONTWRITEBYTECODE=1
ENV OPENAI_API_KEY=
ENV OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ENV OPENAI_MODEL=qwen-plus
ENV JWT_SECRET_KEY=your-secret-key-here
ENV DATABASE_URL=sqlite:////app/internal_db/huntingagent.db
ENV TOOL_TIMEOUT=30
ENV TOOL_MAX_MEMORY=256M

RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

COPY skills/ skills/

RUN mkdir -p logs static internal_db

COPY frontend/dist/ static/

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]