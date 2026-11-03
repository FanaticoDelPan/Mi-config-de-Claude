# Conector del mail de la EMPRESA (solo lectura) y pase de envío aparte

Conector MCP local para que Claude lea el Gmail de la empresa (Google Workspace de ClearSky). El oficial
de claude.ai solo acepta la cuenta de Google del mismo mail que la cuenta de Claude, que es la personal.

**Para qué:** decirle al dueño si un aviso de Google o de un proveedor es importante o de rutina, y bajar
plantillas de migración para trabajarlas en otro proyecto. **El mail personal va por el conector oficial**
(lectura libre; mandar, solo si lo pide y confirmándolo antes). **El de la empresa, solo lectura.**

Además guarda un **segundo pase, solo para mandar**, que usa únicamente el vigilante de la migración
automática (`Migracion-SkyIA\automatico\`) para mandarle a Hernán lo que está listo. El conector MCP nunca lo
lee.

## Cómo está armado

- **El candado es de Google:** el pase del conector tiene `gmail.readonly`. Con ese pase no se puede mandar,
  borrar, mover ni marcar nada, aunque el código lo intentara. Herramientas: `buscar_correos`,
  `leer_correo` (con verificación SPF/DKIM/DMARC del remitente), `leer_hilo`, `bajar_adjunto` (a
  `Descargas\Adjuntos mail empresa`, sin pisar).
- **Dos pases, dos archivos** (`boveda.py`), cifrados con DPAPI del USUARIO en `%LOCALAPPDATA%\mcp-mail-empresa\`:
  `llave.dpapi` (lectura) y `llave-envio.dpapi` (envío: `gmail.send` más `openid`/`userinfo.email`, que solo
  dicen de quién es la cuenta). `conectar.py` rechaza guardar un pase al que Google le dio algún permiso que no
  se pidió. Nunca van al repo (`.gitignore` excluye `*.json`). Se revocan desde la cuenta de Google →
  Seguridad → Apps de terceros con acceso.
- ⚠ **Límite:** DPAPI del usuario lo abre cualquier programa que corra como ese usuario en esa máquina. El
  candado contra mandar de más no es el cifrado: es que el conector solo lee `llave.dpapi`, y que el vigilante
  tiene el destinatario fijo en su código.
- **Dónde los busca:** la app de escritorio de Claude virtualiza AppData, así que un pase conectado desde un
  chat queda en `%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Local\mcp-mail-empresa\`. `boveda.ruta()` mira
  los dos lugares y usa el más nuevo; `guardar()` escribe en el de siempre. Por eso **conectar desde una
  consola común** (no desde un chat): así el pase queda donde lo ven la tarea programada y cualquier consola.
- **No hay contraseña guardada.** El dueño entra por la página de Google; Google entrega un pase permanente
  (refresh token). **Por qué no una contraseña de aplicación:** da acceso IMAP/SMTP completo (leer, borrar y
  mandar), exige verificación en dos pasos y Workspace suele tenerla apagada.
- `conectar.py` verifica que la cuenta con la que se entró sea la pedida (no la personal) antes de guardar.
  Reusa el cliente OAuth de un pase ya guardado; solo si no hay ninguno pide el JSON y lo borra al terminar.
- Registrado a nivel USUARIO (`claude mcp add --scope user mail-empresa`): anda en cualquier proyecto.

## Instalar en una máquina

1. `py -3.14 -m venv .venv` y `.venv\Scripts\python.exe -m pip install mcp google-api-python-client google-auth-oauthlib`
   (mcp 2.x: la clase es `MCPServer`, ya no `FastMCP`).
2. Cliente OAuth en Google Cloud (proyecto de la organización clearsky.com.ar): habilitar la Gmail API,
   pantalla de consentimiento **Interna** (así el pase no vence a los 7 días como en una app externa «de
   prueba») y crear un ID de cliente **App de escritorio**; bajar el JSON.
3. Desde una consola común, en esta carpeta: `.venv\Scripts\python.exe conectar.py <cuenta@clearsky.com.ar>`
   (la primera vez toma el `client_secret*.json` más nuevo de Descargas; para reconectar, el mismo comando).
4. Solo en la máquina que corre la migración automática: `.venv\Scripts\python.exe conectar.py
   <cuenta@clearsky.com.ar> --envio`.
5. `claude mcp add --scope user mail-empresa -- <ruta>\.venv\Scripts\python.exe <ruta>\servidor.py`

Tests: `.venv\Scripts\python.exe -m unittest test_boveda -v` (en esta carpeta).
