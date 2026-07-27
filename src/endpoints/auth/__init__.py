"""
Router agregador del módulo de autenticación.

Organizado por FLUJO, no por entidad: CodigoVerificacion no tiene rutas
propias porque es una herramienta de apoyo interna, usada por registro.py
y password.py, no una entidad que el frontend consulte directamente.
"""

from fastapi import APIRouter

from src.endpoints.auth import (
    Login as login,
    Password as password,
    Registro as registro,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

router.include_router(registro.router)
router.include_router(login.router)
router.include_router(password.router)
