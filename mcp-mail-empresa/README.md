# Conector del mail de la EMPRESA (solo lectura)

Conector MCP local para que Claude lea el Gmail de la empresa (Google Workspace de Clear Sky). El oficial
de claude.ai solo acepta la cuenta de Google del mismo mail que la cuenta de Claude, que es la personal.

**Para qué:** decirle al dueño si un aviso de Google o de un proveedor es importante o de rutina, y bajar
plantillas de migración para trabajarlas en otro proyecto. **El mail personal va por el conector oficial**
(lectura libre; mandar, solo si lo pide y confirmándolo antes). **El de la empresa, solo lectura.**

## Cómo está armado

- **El candado es de Google:** el permiso pedido es `gmail.readonly`. Con ese pase no se puede mandar,
  borrar, mover ni marcar nada, aunque el código lo intentara. Herramientas: `buscar_correos`,
  `leer_correo` (con verificación SPF/DKIM/DMARC del remitente), `leer_hilo`, `bajar_adjunto` (a
  `Descargas\Adjuntos mail empresa`, sin pisar).
- **No hay contraseña guardada.** El dueño entra una vez por la página de Google; Google entrega un pase de
  lectura (refresh token) que `boveda.py` guarda cifrado con DPAPI del USUARIO en
  `%LOCALAPPDATA%\mcp-mail-empresa\llave.dpapi`. Nunca va al repo (`.gitignore` excluye `*.json`).
  Se revoca desde la cuenta de Google → Seguridad → Apps de terceros con acceso.
- **Por qué no una contraseña de aplicación:** da acceso IMAP/SMTP completo (leer, borrar y mandar), exige
  verificación en dos pasos y Workspace suele tenerla apagada.
- `conectar.py` verifica que la cuenta con la que se entró sea la pedida (no la personal) antes de guardar,
  y borra el JSON del cliente descargado.
- Registrado a nivel USUARIO (`claude mcp add --scope user mail-empresa`): anda en cualquier proyecto.

## Instalar en una máquina

1. `py -3.14 -m venv .venv` y `.venv\Scripts\python.exe -m pip install mcp google-api-python-client google-auth-oauthlib`
   (mcp 2.x: la clase es `MCPServer`, ya no `FastMCP`).
2. Cliente OAuth en Google Cloud (proyecto de la organización clearsky.com.ar): habilitar la Gmail API,
   pantalla de consentimiento **Interna** (así el pase no vence a los 7 días como en una app externa «de
   prueba») y crear un ID de cliente **App de escritorio**; bajar el JSON.
3. `.venv\Scripts\python.exe conectar.py <cuenta@clearsky.com.ar>` (toma el `client_secret*.json` más nuevo
   de Descargas). Para reconectar después alcanza el mismo comando sin JSON.
4. `claude mcp add --scope user mail-empresa -- <ruta>\.venv\Scripts\python.exe <ruta>\servidor.py`
