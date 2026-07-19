"""
Configuración de base de datos.
- Producción/CI: usa DATABASE_URL (PostgreSQL/Neon).
- Desarrollo local: usa SQLite si DATABASE_URL no está definida.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
import logging

DATABASE_URL = os.environ.get("DATABASE_URL")
logging.warning(
    f"DATABASE_URL cargada: {DATABASE_URL[:30] if DATABASE_URL else 'NONE'}"
)

if not DATABASE_URL:
    db_path = Path(__file__).resolve().parents[2] / "dev.db"
    DATABASE_URL = f"sqlite:///{db_path.as_posix()}"

# SSL: "require" para Neon en producción; "disable" para PostgreSQL local/CI
_ssl_mode = os.getenv("SSL_MODE", "require")

_engine_kwargs = {
    "echo": False,  # Cambiar a True para ver consultas SQL
    "pool_pre_ping": True,  # Verificar conexión antes de usar
    "pool_recycle": 300,  # Reciclar conexiones cada 5 minutos
}

if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["connect_args"] = {"sslmode": _ssl_mode}

# Crear el motor de SQLAlchemy
engine = create_engine(DATABASE_URL, **_engine_kwargs)

# Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()


def get_db():
    """
    Generador de sesiones de base de datos
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Crear todas las tablas definidas en los modelos
    """
    Base.metadata.create_all(bind=engine)
