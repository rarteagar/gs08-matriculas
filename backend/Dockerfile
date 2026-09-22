# syntax=docker/dockerfile:1.7
# ============================================================
# GS08 - Matriculas | API FastAPI (Python 3.12)
# Imagen runtime de 2 etapas: deps (compila/instala) -> runtime (usuario no root)
# Build:  docker build -t gs08-api:local ./backend
# ============================================================

FROM python:3.12.14-slim-bookworm AS deps
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /build
# Se instala en un venv aislado para copiarlo limpio a la etapa runtime
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

FROM python:3.12.14-slim-bookworm AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"
# curl solo como herramienta de healthcheck; usuario sin privilegios
RUN apt-get update \
 && apt-get install --no-install-recommends -y curl \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --create-home app

COPY --from=deps /opt/venv /opt/venv
WORKDIR /app
COPY --chown=app:app . .
USER app
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
