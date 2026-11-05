from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from src.database.config import Base


class TokenRevocado(Base):
    """Token (access o refresh) invalidado al cerrar sesión (HU35).

    Se guarda solo el SHA-256 del token, nunca el token. `expira_en` permite
    borrar la fila cuando el token ya habría caducado por sí solo.

    Attributes:
        token_hash (str): SHA-256 hexadecimal del JWT (Primary Key).
        usuario_id (UUID): Dueño del token (el claim `sub`).
        tipo (str): 'access' o 'refresh'.
        expira_en (datetime): Expiración original del token (UTC).
        fecha_revocacion (datetime): Cuándo se cerró la sesión (UTC).
    """

    __tablename__ = "tokens_revocados"

    token_hash = Column(String(64), primary_key=True)
    usuario_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tipo = Column(String(10), nullable=False)
    expira_en = Column(DateTime, nullable=False, index=True)
    fecha_revocacion = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
