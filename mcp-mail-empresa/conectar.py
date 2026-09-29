"""Conecta (o reconecta) el mail de la empresa, con permiso de SOLO LECTURA.

Uso:  .venv\\Scripts\\python.exe conectar.py <cuenta@empresa>  [ruta-del-json-del-cliente]

Sin ruta, toma el `client_secret*.json` más nuevo de Descargas. Abre el navegador para entrar con la cuenta,
verifica que sea ESA cuenta (no la personal), guarda la llave cifrada en el perfil y borra el JSON descargado.
"""

import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import boveda

PERMISO = ["https://www.googleapis.com/auth/gmail.readonly"]


def _json_del_cliente(argumento: str | None) -> Path:
    if argumento:
        return Path(argumento)
    descargas = Path.home() / "Downloads"
    candidatos = sorted(descargas.glob("client_secret*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidatos:
        sys.exit(f"No encontré ningún client_secret*.json en {descargas}. Pasame la ruta del archivo.")
    return candidatos[0]


def main() -> None:
    if len(sys.argv) < 2 or "@" not in sys.argv[1]:
        sys.exit(__doc__)
    cuenta = sys.argv[1].strip().lower()
    anterior = boveda.leer()

    if len(sys.argv) > 2 or not anterior:
        origen = _json_del_cliente(sys.argv[2] if len(sys.argv) > 2 else None)
        cliente = json.loads(origen.read_text(encoding="utf-8"))
    else:
        # Reconectar sin volver a bajar el cliente: se reusa el guardado.
        origen = None
        cliente = {"installed": {
            "client_id": anterior["client_id"], "client_secret": anterior["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }}

    flujo = InstalledAppFlow.from_client_config(cliente, PERMISO)
    credenciales = flujo.run_local_server(
        port=0, login_hint=cuenta, prompt="consent",
        authorization_prompt_message="Se abrió el navegador: entrá con {url}".replace("{url}", cuenta),
        success_message="Listo: ya podés cerrar esta pestaña y volver a Claude.",
    )

    perfil = build("gmail", "v1", credentials=credenciales, cache_discovery=False).users().getProfile(
        userId="me").execute()
    real = perfil["emailAddress"].lower()
    if real != cuenta:
        sys.exit(f"Entraste con {real}, pero el conector es para {cuenta}. No guardé nada: probá de nuevo.")
    if not credenciales.refresh_token:
        sys.exit("Google no devolvió la llave permanente. No guardé nada: probá de nuevo.")

    boveda.guardar({
        "cuenta": real,
        "client_id": credenciales.client_id,
        "client_secret": credenciales.client_secret,
        "refresh_token": credenciales.refresh_token,
    })
    if origen is not None:
        origen.unlink(missing_ok=True)
    print(f"Conectado {real} con permiso de solo lectura ({perfil.get('messagesTotal', '?')} correos).")


if __name__ == "__main__":
    main()
