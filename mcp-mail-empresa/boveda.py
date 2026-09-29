"""Guarda el pase de lectura del mail de la empresa cifrado con DPAPI del USUARIO de Windows.

Solo este usuario, en esta máquina, puede descifrarlo: copiar el archivo a otra PC o leerlo desde otra cuenta
no sirve. Vive en el perfil (LOCALAPPDATA), nunca en el repo.
"""

import ctypes
import ctypes.wintypes as wt
import json
import os
from pathlib import Path

CARPETA = Path(os.environ["LOCALAPPDATA"]) / "mcp-mail-empresa"
ARCHIVO = CARPETA / "llave.dpapi"


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wt.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _a_blob(datos: bytes) -> tuple[_Blob, ctypes.Array]:
    buffer = ctypes.create_string_buffer(datos, len(datos))
    return _Blob(len(datos), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer


def _de_blob(blob: _Blob) -> bytes:
    try:
        return ctypes.string_at(blob.pbData, blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob.pbData)


def _cifrar(datos: bytes) -> bytes:
    entrada, _buffer = _a_blob(datos)
    salida = _Blob()
    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(entrada), "mcp-mail-empresa", None, None, None, 0, ctypes.byref(salida)
    ):
        raise ctypes.WinError()
    return _de_blob(salida)


def _descifrar(datos: bytes) -> bytes:
    entrada, _buffer = _a_blob(datos)
    salida = _Blob()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(entrada), None, None, None, None, 0, ctypes.byref(salida)
    ):
        raise ctypes.WinError()
    return _de_blob(salida)


def guardar(contenido: dict) -> None:
    CARPETA.mkdir(parents=True, exist_ok=True)
    ARCHIVO.write_bytes(_cifrar(json.dumps(contenido).encode("utf-8")))


def leer() -> dict | None:
    if not ARCHIVO.exists():
        return None
    return json.loads(_descifrar(ARCHIVO.read_bytes()).decode("utf-8"))
