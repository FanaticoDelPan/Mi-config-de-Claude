"""Guarda los pases del mail de la empresa cifrados con DPAPI del USUARIO de Windows.

Solo este usuario, en esta máquina, puede descifrarlos: copiar el archivo a otra PC o leerlo desde otra cuenta
no sirve. Viven en el perfil (LOCALAPPDATA), nunca en el repo.

Dos pases, en archivos separados, para que el conector de lectura nunca tenga en la mano el de mandar:
- `lectura` (`llave.dpapi`): permiso `gmail.readonly`. Lo usan el conector MCP y el vigilante de migraciones.
- `envio` (`llave-envio.dpapi`): permiso `gmail.send` y nada más. Lo usa SOLO el vigilante de migraciones
  (Migracion-SkyIA), que manda a un destinatario fijo en su código.

Dónde se buscan: la app de escritorio de Claude es un paquete MSIX y virtualiza AppData para todo lo que lanza,
así que un pase guardado desde un chat queda en `LOCALAPPDATA\\Packages\\Claude_*\\LocalCache\\Local\\...` y una
consola común o una tarea programada no lo ve por la ruta de siempre. `ruta()` mira los dos lugares y se queda
con el más nuevo; `guardar()` escribe siempre en `LOCALAPPDATA\\mcp-mail-empresa` (desde una consola común, el
lugar real). Un pase se lee donde está: nunca se copia ni se mueve.
"""

import ctypes
import ctypes.wintypes as wt
import json
import os
from pathlib import Path

NOMBRE_CARPETA = "mcp-mail-empresa"
ARCHIVOS = {"lectura": "llave.dpapi", "envio": "llave-envio.dpapi"}


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


def _local() -> Path:
    return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")


def carpeta() -> Path:
    """Donde `guardar()` escribe."""
    return _local() / NOMBRE_CARPETA


def _archivo(tipo: str) -> str:
    if tipo not in ARCHIVOS:
        raise ValueError(f"tipo de pase desconocido: {tipo!r} (es 'lectura' o 'envio')")
    return ARCHIVOS[tipo]


def candidatas(tipo: str = "lectura") -> list[Path]:
    """Los lugares donde puede estar el pase: el de siempre y la copia privada de la app de Claude."""
    nombre = _archivo(tipo)
    local = _local()
    return [local / NOMBRE_CARPETA / nombre,
            *sorted((local / "Packages").glob(f"Claude_*/LocalCache/Local/{NOMBRE_CARPETA}/{nombre}"))]


def ruta(tipo: str = "lectura") -> Path | None:
    """El pase que existe; si hay más de uno, el más nuevo (el último que se conectó)."""
    existentes = [c for c in candidatas(tipo) if c.is_file()]
    return max(existentes, key=lambda c: c.stat().st_mtime) if existentes else None


def guardar(contenido: dict, tipo: str = "lectura") -> Path:
    destino = carpeta() / _archivo(tipo)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(_cifrar(json.dumps(contenido).encode("utf-8")))
    return destino


def leer(tipo: str = "lectura") -> dict | None:
    origen = ruta(tipo)
    if origen is None:
        return None
    return json.loads(_descifrar(origen.read_bytes()).decode("utf-8"))
