"""
Aplicación FastAPI - Proyecto Objetos Perdidos
Ejecutar con: uvicorn main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import Response

from src.database.config import create_tables

# Importamos los routers que creamos juntos
from src.endpoints import (
    ActaEntrega,
    AuditoriaLog,
    PosibleCoincidencia,
    Reclamos,
    RespuestSeguridad,
    Reclamos,
)

# Importaciones de configuración y manejo de errores (basado en tu estructura)
from src.core.config import get_settings
from src.core.exceptions import AppException
from src.core.error_handlers import (
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)

# Importar modelos para que Base.metadata los conozca al crear las tablas
import src.entities.Reclamos  # noqa: F401
import src.entities.RespuestaSeguridad  # noqa: F401
import src.entities.PosibleCoincidencia  # noqa: F401
import src.entities.ActaEntrega  # noqa: F401
import src.entities.AuditoriaLog  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa la base de datos al arrancar el servidor."""
    create_tables()
    yield


app = FastAPI(
    title="API Objetos Perdidos",
    description="Backend para el sistema de objetos en custodia y reclamos",
    version="1.0.0",
    lifespan=lifespan,
)

_settings = get_settings()

# Configuración de CORS (Quién puede consultar tu API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Configuración de Cabeceras de Seguridad
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response: Response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    # Nota: Agregué la URL de Supabase para que no te bloquee las imágenes
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "connect-src 'self' https://*.supabase.co; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://*.supabase.co; "
        "frame-ancestors 'none'; "
        "base-uri 'self';"
    )

    return response


# Registrar handlers globales de errores
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Registrar los Routers (Endpoints) de nuestro proyecto
app.include_router(Reclamos.router)
app.include_router(RespuestSeguridad.router)
app.include_router(PosibleCoincidencia.router)
app.include_router(ActaEntrega.router)
app.include_router(AuditoriaLog.router)

# Si tienes routers de Usuarios o ObjetosEnCustodia, agrégalos aquí también.


@app.get("/")
def inicio():
    """Endpoint raíz para comprobar el estado de la API."""
    return {
        "success": True,
        "data": {"mensaje": "API de Objetos Perdidos funcionando", "docs": "/docs"},
    }
