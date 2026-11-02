"""Genera archivos CSV y Excel a partir de (columnas, filas)."""

import csv
import io
from datetime import date, datetime
from typing import Any, Iterable, Sequence

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

# Una celda de texto que empiece así sería interpretada como fórmula al abrirla
# en Excel/LibreOffice (inyección de fórmulas con texto escrito por los usuarios).
_PELIGROSOS = ("=", "+", "-", "@", "\t", "\r")


def _celda(valor: Any) -> Any:
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, datetime):
        return valor.strftime("%Y-%m-%d %H:%M")
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, (int, float)):
        return valor
    texto = str(getattr(valor, "value", valor))
    return "'" + texto if texto.startswith(_PELIGROSOS) else texto


def a_csv(columnas: Sequence[str], filas: Iterable[Sequence[Any]]) -> bytes:
    """CSV en UTF-8 con BOM, para que Excel respete las tildes."""
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow([_celda(c) for c in columnas])
    for fila in filas:
        escritor.writerow([_celda(v) for v in fila])
    return ("﻿" + salida.getvalue()).encode("utf-8")


def a_xlsx(columnas: Sequence[str], filas: Iterable[Sequence[Any]], titulo: str) -> bytes:
    libro = Workbook()
    hoja = libro.active
    hoja.title = titulo[:31]
    hoja.append([_celda(c) for c in columnas])
    for celda in hoja[1]:
        celda.font = Font(bold=True)
    anchos = [len(str(c)) for c in columnas]
    for fila in filas:
        valores = [_celda(v) for v in fila]
        hoja.append(valores)
        for i, v in enumerate(valores):
            anchos[i] = max(anchos[i], len(str(v)))
    for i, ancho in enumerate(anchos, start=1):
        hoja.column_dimensions[get_column_letter(i)].width = min(ancho + 2, 60)
    hoja.freeze_panes = "A2"
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()
