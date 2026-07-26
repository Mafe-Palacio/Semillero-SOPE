from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy.orm import Session
from sqlalchemy import text  # Importamos 'text' para ejecutar SQL directo
from src.database.config import (
    get_db,
)  # Asegúrate de que esta ruta coincida con tu proyecto

app = FastAPI(
    title="API de Objetos Perdidos",
    description="Backend para el sistema de objetos en custodia",
    version="1.0.0",
)


@app.get("/test-db", tags=["Pruebas de Sistema"])
def probar_conexion_bd(db: Session = Depends(get_db)):
    """
    Endpoint para verificar que la conexión a la base de datos local funciona correctamente.
    Intenta ejecutar una consulta SQL básica (SELECT 1).
    """
    try:
        # Intentamos ejecutar una consulta muy simple en la base de datos
        db.execute(text("SELECT 1"))

        # Si no hay errores en la línea anterior, la conexión es un éxito
        return {
            "exito": True,
            "mensaje": "¡Conexión a la base de datos exitosa! Tu .env y PostgreSQL funcionan perfecto.",
        }
    except Exception as e:
        # Si la contraseña, usuario o base de datos estuvieran mal, caeríamos aquí
        return {
            "exito": False,
            "mensaje": "Hubo un error al conectar con la base de datos.",
            "detalle_del_error": str(e),
        }
