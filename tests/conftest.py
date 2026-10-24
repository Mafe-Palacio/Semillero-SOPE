import os
import sys
import uuid
from datetime import date
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite://")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main
from src.core.auth import create_access_token
from src.core.config import get_settings
from src.database.config import Base, get_db
from src.entities.ObjetoEnCustodia import ObjetoEnCustodia
from src.entities.PuntoEntrega import PuntoEntrega
from src.entities.Sede import Sede
from src.entities.Usuario import Usuario


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def client(db):
    def _get_db():
        yield db

    main.app.dependency_overrides[get_db] = _get_db
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


@pytest.fixture()
def sede(db):
    s = Sede(nombre="Fraternidad", codigo="FRAT")
    db.add(s)
    db.commit()
    return s


@pytest.fixture()
def punto(db, sede):
    p = PuntoEntrega(sede_id=sede.sede_id, nombre="Oficina OPE", tipo="OFICINA")
    db.add(p)
    db.commit()
    return p


def _usuario(db, n, rol="USER", celular="3001234567", sede_id=None):
    u = Usuario(
        nombre_completo=f"Usuario {n}",
        cedula=f"100{n}",
        correo=f"u{n}@correo.itm.edu.co",
        hashed_password="x",
        rol=rol,
        tipo_vinculacion="ESTUDIANTE",
        celular=celular,
        sede_id=sede_id,
        is_verified=True,
    )
    db.add(u)
    db.commit()
    return u


@pytest.fixture()
def make_user(db):
    counter = iter(range(1, 1000))

    def _make(**kw):
        return _usuario(db, next(counter), **kw)

    return _make


@pytest.fixture()
def auth():
    def _auth(user):
        token = create_access_token(
            subject=user.usuario_id, correo=user.correo, rol=user.rol, settings=get_settings()
        )
        return {"Authorization": f"Bearer {token}"}

    return _auth


@pytest.fixture()
def objeto(db, punto, make_user):
    admin = make_user(rol="ADMIN", sede_id=punto.sede_id)
    o = ObjetoEnCustodia(
        admin_id=admin.usuario_id,
        categoria="LLAVES",
        descripcion="Llavero",
        lugar_origen_id=punto.puntoEntrega_id,
        fecha_ingreso=date.today(),
    )
    db.add(o)
    db.commit()
    return o
