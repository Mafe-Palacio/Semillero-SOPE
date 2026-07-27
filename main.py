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

# Routers de tu compañera
from src.endpoints import (
    ActaEntrega,
    AuditoriaLog,
    PosibleCoincidencia,
    Reclamos,
    RespuestSeguridad,
)

# Routers propios
from src.endpoints import (
    CodigoVerificacion,
    ObjetoEnCustodia,
    PreguntaSeguridad,
    PublicacionEncontrado,
    PuntoEntrega,
    ReportePerdida,
    Sede,
    Ubicacion,
    Usuario,
)
from src.endpoints.auth import router as auth_router

# Importaciones de configuración y manejo de errores (basado en tu estructura)
from src.core.config import get_settings
from src.core.exceptions import AppException
from src.core.error_handlers import (
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)

# Importar TODOS los modelos para que Base.metadata los conozca al crear
# las tablas (create_tables() es un no-op si ya existen en Supabase, pero
# igual necesita conocer las clases para no fallar por referencias FK
# cruzadas entre entidades de distintos módulos).
import src.entities.Sede  # noqa: F401
import src.entities.Ubicacion  # noqa: F401
import src.entities.PuntoEntrega  # noqa: F401
import src.entities.Usuario  # noqa: F401
import src.entities.CodigoVerificacion  # noqa: F401
import src.entities.ReportePerdida  # noqa: F401
import src.entities.PublicacionEncontrado  # noqa: F401
import src.entities.ObjetoEnCustodia  # noqa: F401
import src.entities.PreguntaSeguridad  # noqa: F401
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

# Autenticación primero (no requiere token, registro/login/recuperación)
app.include_router(auth_router)


app.include_router(Reclamos.router)
app.include_router(RespuestSeguridad.router)
app.include_router(PosibleCoincidencia.router)
app.include_router(ActaEntrega.router)
app.include_router(AuditoriaLog.router)

# Routers propios
app.include_router(Sede.router)
app.include_router(Ubicacion.router)
app.include_router(PuntoEntrega.router)
app.include_router(Usuario.router)
app.include_router(CodigoVerificacion.router)
app.include_router(ReportePerdida.router)
app.include_router(PublicacionEncontrado.router)
app.include_router(ObjetoEnCustodia.router)
app.include_router(PreguntaSeguridad.router)


@app.get("/")
def inicio():
    """Endpoint raíz para comprobar el estado de la API."""
    return {
        "success": True,
        "data": {"mensaje": "API de Objetos Perdidos funcionando", "docs": "/docs"},
    }
