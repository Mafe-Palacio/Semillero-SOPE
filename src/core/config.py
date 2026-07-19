"""
Configuración centralizada (JWT, CORS) desde variables de entorno.
En producción: JWT_SECRET_KEY debe ser una cadena larga y aleatoria (p. ej. openssl rand -hex 32).
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ajustes cargados desde el entorno y opcionalmente desde un archivo `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    jwt_secret_key: str = Field(
        default="",
        description="Clave HMAC para firmar JWT; obligatoria en entornos reales.",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60,
        ge=5,
        le=24 * 60,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    # Orígenes permitidos separados por coma. Con credenciales no se puede usar "*".
    cors_origins: str = Field(
        default=(
            "http://localhost:3000,"
            "http://localhost:4200,"
            "http://localhost:5173,"
            "http://127.0.0.1:3000,"
            "http://127.0.0.1:4200,"
            "http://127.0.0.1:5173"
        ),
        validation_alias="CORS_ORIGINS",
    )

    @field_validator("jwt_secret_key")
    @classmethod
    def jwt_secret_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            # Valor solo     para desarrollo local; sustituir en .env antes de desplegar.
            return "dev-insecure-jwt-secret-replace-with-JWT_SECRET_KEY-in-env"
        return v.strip()

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
