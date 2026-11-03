"""Conecta (o reconecta) el mail de la empresa. Dos pases separados (ver `boveda.py`):

    .venv\\Scripts\\python.exe conectar.py <cuenta@empresa>            pase de LECTURA (gmail.readonly)
    .venv\\Scripts\\python.exe conectar.py <cuenta@empresa> --envio    pase de ENVÍO (gmail.send y nada más)
    ... [ruta-del-json-del-cliente]                                    con otro cliente OAuth

Sin ruta reusa el cliente OAuth ya guardado (el de cualquiera de los dos pases, esté donde esté); si no hay
ninguno, toma el `client_secret*.json` más nuevo de Descargas y lo borra al terminar. Abre el navegador para
entrar con la cuenta, verifica que sea ESA cuenta (no la personal) y que Google haya dado SOLO el permiso
pedido, y guarda el pase cifrado en el perfil.
"""

import base64
import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import boveda

LECTURA = "https://www.googleapis.com/auth/gmail.readonly"
ENVIO = "https://www.googleapis.com/auth/gmail.send"
# Para el pase de envío, la identidad sale del token de OpenID: con gmail.send solo no se puede preguntar a
# Gmail de quién es la casilla. `openid` y `userinfo.email` dan el mail de la cuenta y nada del correo.
IDENTIDAD = ["openid", "https://www.googleapis.com/auth/userinfo.email"]
PERMISOS = {"lectura": [LECTURA], "envio": [ENVIO, *IDENTIDAD]}


def _json_del_cliente(argumento: str | None) -> Path:
    if argumento:
        return Path(argumento)
    descargas = Path.home() / "Downloads"
    candidatos = sorted(descargas.glob("client_secret*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidatos:
        sys.exit(f"No encontré ningún client_secret*.json en {descargas} ni un pase guardado del que sacar el "
                 "cliente. Pasame la ruta del archivo.")
    return candidatos[0]


def _cliente_guardado(tipo: str) -> dict | None:
    """El cliente OAuth de un pase ya guardado: primero el del mismo tipo, después el otro."""
    for cual in (tipo, *(t for t in boveda.ARCHIVOS if t != tipo)):
        anterior = boveda.leer(cual)
        if anterior and anterior.get("client_id") and anterior.get("client_secret"):
            return {"installed": {
                "client_id": anterior["client_id"], "client_secret": anterior["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }}
    return None


def _mail_del_id_token(id_token: str | None) -> str | None:
    """El `email` del token de OpenID. Llegó directo de Google por TLS en el canje del código: no hace falta
    verificar la firma para leer de quién es."""
    if not id_token:
        return None
    try:
        cuerpo = id_token.split(".")[1]
        datos = json.loads(base64.urlsafe_b64decode(cuerpo + "=" * (-len(cuerpo) % 4)))
    except (IndexError, ValueError):
        return None
    if not datos.get("email_verified", True):
        return None
    return (datos.get("email") or "").lower() or None


def permisos_de_mas(tipo: str, otorgados) -> list[str]:
    """Lo que Google dio y no se pidió (p. ej. por autorización incremental): con algo de más, no se guarda."""
    if isinstance(otorgados, str):
        otorgados = otorgados.split()
    return sorted(set(otorgados or []) - set(PERMISOS[tipo]))


def main() -> None:
    argumentos = [a for a in sys.argv[1:] if a != "--envio"]
    tipo = "envio" if "--envio" in sys.argv[1:] else "lectura"
    if not argumentos or "@" not in argumentos[0]:
        sys.exit(__doc__)
    cuenta = argumentos[0].strip().lower()
    ruta_json = argumentos[1] if len(argumentos) > 1 else None

    origen = None
    cliente = None if ruta_json else _cliente_guardado(tipo)
    if cliente is None:
        origen = _json_del_cliente(ruta_json)
        cliente = json.loads(origen.read_text(encoding="utf-8"))

    flujo = InstalledAppFlow.from_client_config(cliente, PERMISOS[tipo])
    credenciales = flujo.run_local_server(
        port=0, login_hint=cuenta, prompt="consent",
        authorization_prompt_message="Se abrió el navegador: entrá con {url}".replace("{url}", cuenta),
        success_message="Listo: ya podés cerrar esta pestaña y volver a la consola.",
    )

    de_mas = permisos_de_mas(tipo, credenciales.granted_scopes)
    if de_mas:
        sys.exit(f"Google dio permisos que no pedí ({', '.join(de_mas)}). No guardé nada: quitale el acceso a la "
                 "app en la cuenta de Google (Seguridad → Apps de terceros) y probá de nuevo.")
    if tipo == "lectura":
        perfil = build("gmail", "v1", credentials=credenciales, cache_discovery=False).users().getProfile(
            userId="me").execute()
        real = perfil["emailAddress"].lower()
        detalle = f"permiso de solo lectura ({perfil.get('messagesTotal', '?')} correos)"
    else:
        real = _mail_del_id_token(credenciales.id_token)
        if not real:
            sys.exit("Google no dijo con qué cuenta entraste. No guardé nada: probá de nuevo.")
        detalle = "permiso de solo MANDAR (no puede leer, borrar ni mover nada)"
    if real != cuenta:
        sys.exit(f"Entraste con {real}, pero el pase es para {cuenta}. No guardé nada: probá de nuevo.")
    if not credenciales.refresh_token:
        sys.exit("Google no devolvió la llave permanente. No guardé nada: probá de nuevo.")

    destino = boveda.guardar({
        "cuenta": real,
        "client_id": credenciales.client_id,
        "client_secret": credenciales.client_secret,
        "refresh_token": credenciales.refresh_token,
        "permisos": PERMISOS[tipo],
    }, tipo)
    if origen is not None:
        origen.unlink(missing_ok=True)
    print(f"Conectado {real} con {detalle}. Guardado en {destino}.")


if __name__ == "__main__":
    main()
