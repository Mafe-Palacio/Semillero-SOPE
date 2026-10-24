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
        default=15,
        ge=5,
        le=24 * 60,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        validation_alias="REFRESH_TOKEN_EXPIRE_DAYS",
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

    # SMTP para el Notification Dispatcher (correos transaccionales: OTP,
    # Smart Match, citas presenciales, cierre de reclamo, bloqueo de cuenta).
    smtp_host: str = Field(default="smtp.gmail.com", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_user: str = Field(default="", validation_alias="SMTP_USER")
    smtp_pass: str = Field(default="", validation_alias="SMTP_PASS")
    smtp_from: str = Field(default="", validation_alias="SMTP_FROM")

    # Cloudinary (carga de imágenes, HU28). Sin credenciales, POST /imagenes responde 503.
    cloudinary_cloud_name: str = Field(
        default="", validation_alias="CLOUDINARY_CLOUD_NAME"
    )
    cloudinary_api_key: str = Field(default="", validation_alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(
        default="", validation_alias="CLOUDINARY_API_SECRET"
    )
    # Hosts permitidos para las URL de imagen, separados por coma (ej. res.cloudinary.com).
    # Vacío = se acepta cualquier URL https.
    image_allowed_hosts: str = Field(default="", validation_alias="IMAGE_ALLOWED_HOSTS")

    @field_validator("jwt_secret_key")
    @classmethod
    def jwt_secret_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            # Valor solo     para desarrollo local; sustituir en .env antes de desplegar.
            return "dev-insecure-jwt-secret-replace-with-JWT_SECRET_KEY-in-env"
        return v.strip()

    def image_allowed_hosts_list(self) -> list[str]:
        return [
            h.strip().lower() for h in self.image_allowed_hosts.split(",") if h.strip()
        ]

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
