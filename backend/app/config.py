# ============================================================
# GS08 · Matrículas y Notas | app/config.py
# Autor: @dev | T1.1 | Sprint 1
# Configuración leída del entorno. Los nombres de las variables son el
# contrato de @devops (docs/devops/plan-contenedores-ci.md §3): DATABASE_URL,
# SECRET_KEY, ENVIRONMENT, LOG_LEVEL (+ ACCESS_TOKEN_EXPIRE_MINUTES de compose).
# ============================================================
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # postgresql+psycopg:// (driver síncrono): es el que fija docker-compose.yml
    database_url: str = "postgresql+psycopg://gs08:gs08_dev_pwd@localhost:5432/gs08_matriculas"
    secret_key: str = "cambiar-esta-clave-en-produccion"
    environment: str = "local"
    log_level: str = "info"
    access_token_expire_minutes: int = 60
    algoritmo_token: str = "HS256"
    origen_cors: str = "http://localhost:5173,http://localhost:8080"

    @property
    def origenes_cors(self) -> list[str]:
        return [o.strip() for o in self.origen_cors.split(",") if o.strip()]


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()


config = obtener_configuracion()
