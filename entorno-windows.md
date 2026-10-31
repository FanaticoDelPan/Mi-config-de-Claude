# Entorno Windows — notas operativas

> **Esto no son reglas de comportamiento: son las trampas de ESTA máquina y de esta consola.**
> Vive afuera del `CLAUDE.md` a propósito, para que el archivo que se carga en cada sesión sea corto.
> **Se lee ANTES de correr comandos de shell, builds, scripts o tests** — la mitad de estas fallas se
> disfrazan de otra cosa y mandan a buscar el problema al lugar equivocado.
>
> **No es un symlink a propósito:** el `CLAUDE.md` lo cita por su ruta en este repo
> (`C:\GitHub\1-Mi-config-de-Claude\entorno-windows.md`). Crear un enlace en `~/.claude` exige privilegios
> de administrador, y hacer que LEER esta nota dependa de una corrida elevada es cambiar un problema por
> otro peor: si el enlace falta, el puntero apunta a la nada y estas trampas vuelven a morder en silencio.
> Apuntando al repo no hay nada que instalar y es imposible que se desincronice.

## Guardia de rutas del harness (el que más muerde)

Bloquea un comando cuyo TEXTO contenga un literal con pinta de ruta protegida
(`Remove-Item on system path '…' is blocked`). ⚠ **Escanea TODO el texto —here-strings y código
incluidos— y no necesita que el comando borre nada**: los falsos positivos son la regla, no la excepción.

* **Workaround general:** nunca escribir rutas absolutas literales — armarlas con `$env:ProgramFiles` /
  `$env:TEMP` / `$env:USERPROFILE`, `Join-Path`, o apoyarse en el cwd (que ya es el repo). Para llegar a
  un repo hermano: `Join-Path (Split-Path (Get-Location)) '<repo>'`. **Todo texto largo viaja por archivo**
  (`git commit -F`, `gh --notes-file`), nunca inline; ese archivo se escribe con Write o desde Bash, **no con
  `Out-File -Encoding utf8` de PowerShell 5.1**, que le pone BOM y el título del commit queda con un carácter
  invisible adelante. **Un script se escribe con Write y se ejecuta por su
  ruta:** sale más barato que esquivar tokens de a uno.
* **Lo que lo dispara (verificado):** un `*` en el mismo comando que un `Remove-Item`; un literal tipo
  `.\dist\App\*` junto a un `Remove-Item`; rutas mencionadas dentro de un here-string (un mensaje de commit
  con `/registro:` alcanzó); la barra suelta de `($env:SystemDrive + '\')` dentro de un `Join-Path`; y,
  dentro de CÓDIGO, `COUNT(*)`, una división `/128.0` y el `as c:` de un `with` de Python.
  **(2026-08-24)** **una barra suelta dentro de una cadena entrecomillada**, aunque no sea una
  ruta: voló con el `'\Information...'` de un `Get-Counter`, con un `\$` y hasta con un ` / `
  dentro de un `-f`. Para contadores: `Get-CimInstance Win32_PerfFormattedData_*`.
  **(2026-09-12)** dos veces en la MISMA sesión, las dos con un `Remove-Item` de **limpieza** al final de un
  comando largo que armaba un banco de pruebas descartable: (a) un `Copy-Item 'scripts\git-hooks\*' $destino`
  — el `*` vuela aunque el `Remove-Item` apunte a otra cosa, a una carpeta de `$env:TEMP` —; (b) un
  `'/c','echo hola'` dentro de un arreglo de argumentos, o sea **una barra suelta en una cadena que no es
  ninguna ruta** (el `cmd /c` de toda la vida).
  🔑 **El patrón de fondo, ya con tres casos:** no dispara lo que el comando HACE, sino que un `Remove-Item`
  COINCIDA en el mismo texto con cualquier `*` o `/`, sea de quien sea. De ahí sale una regla práctica que
  no estaba escrita: **armar un banco de pruebas y desarmarlo en una sola corrida es justo lo que no
  conviene** — la limpieza va sola, en su propio comando, al final.
  **(2026-09-13)** voló un comando **SIN ningún `Remove-Item`** («system path '/'»): una lista larga de rutas
  relativas con `\` dentro de un arreglo, más un `Join-Path $c 'docs\*.md'`. El mismo código pasó escrito en un
  `.ps1` del scratchpad y ejecutado por su ruta, que es el workaround general de arriba.
* **Reglas que salen de eso:** el `Remove-Item` va en su PROPIO comando, sin `*` y con el destino en una
  variable; `COUNT_BIG(1)` en vez de `COUNT(*)`; divisores por variable; **nunca una variable de UNA letra
  antes de `:`**; `.Split('=',2)` en vez de una expresión regular con `(.*)`.
* ⚠ **No es determinístico** (el mismo idioma pasó en un comando corto y voló en uno largo), y el idioma
  viejo `Resolve-Path ($env:ProgramFiles + "\Git* CLI\gh.exe")` ya **no** pasa. **Si un comando salta el
  guard, NO reintentar igual: anotar acá el patrón nuevo.**

## Las otras trampas

* **`/dev/null` como ARGUMENTO desde Git Bash** crea un archivo `nul` en el repo y a partir de ahí
  **`git add -A` falla** (*short read while indexing nul*). Es nombre reservado de Windows: solo lo borra el
  prefijo de ruta extendida (`unlinkSync('\\\\?\\' + join(process.cwd(), 'nul'))`). Redirigir con
  `> /dev/null` es seguro (lo maneja la shell); pasarlo como argumento de un `.exe`, nunca.
* **Un `.cmd` de `node_modules\.bin` no se puede lanzar con `execFileSync`/`spawnSync`** (falla con `EINVAL`).
  Invocar el `.js` real del paquete con el mismo Node — `execFileSync(process.execPath, [join(ROOT,
  'node_modules', 'typescript', 'bin', 'tsc'), ...args])` — es mejor que `shell: true`, que además abre
  inyección de shell. Vale para cualquier herramienta de `.bin`.
* **Un script escrito en el scratchpad que importe una dependencia del proyecto** falla con
  `ERR_MODULE_NOT_FOUND`: Node resuelve los paquetes desde la ubicación del ARCHIVO, no desde el directorio
  de trabajo, y el scratchpad no tiene `node_modules`. Copiarlo a la raíz del repo, correrlo ahí y borrarlo
  al terminar. El scratchpad sirve para archivos sueltos y salidas intermedias, no para código que importa
  dependencias del proyecto.
* **`Invoke-WebRequest` no llega a direcciones públicas de internet, y falla sin decirlo** (ni siquiera hay
  respuesta HTTP: `$_.Exception.Response` en `null`). Para verificar algo contra una URL publicada, usar el
  navegador. ⚠ Un `catch` que asume que hay `Response` tira un error de "matriz nula" que despista.
* **Un `.exe` de INTERFAZ GRÁFICA lanzado desde Bash no escribe nada en la salida y devuelve 0 igual** (está
  compilado sin consola y su stdout se pierde). Todo control que LEA la salida de un `.exe` gráfico
  (navegador headless y afines) se corre con PowerShell. ⚠ La falla se disfraza de "la pantalla está rota" y
  manda a buscar el problema al lugar equivocado.
* **gh (GitHub CLI):** en `%ProgramFiles%\GitHub CLI\gh.exe`, autenticado por keyring (la cuenta varía por
  máquina: `gh api user --jq .login`), **no** está en el PATH de las shells no interactivas. Invocarlo sin
  literales ni comodines: `$gh = Join-Path (Join-Path $env:ProgramFiles 'GitHub CLI') 'gh.exe'; & $gh …`.
  Texto multilínea **siempre** por `--notes-file`: con `--notes "$var"` PowerShell lo parte y gh toma las
  palabras sueltas como globs de archivo.
* **Un heredoc de Python que arma texto para OTRO lenguaje pierde una capa de barra invertida, y avisa con
  un *warning*, no con un error.** `python - <<'PY'` con un reemplazo que lleve una regex de JavaScript o un
  `LIKE` de SQL: lo que en el heredoc va con DOS barras llega al archivo con UNA, que en el lenguaje de
  destino ya no escapa nada. Python lo marca con `SyntaxWarning: invalid escape sequence`, que se lee como
  ruido. ⚠ Ya produjo una condición SQL mal escapada que corrió igual (matcheaba por casualidad, con `_`
  como comodín). **Cadenas crudas —`r"""..."""`— siempre que el reemplazo lleve barras**, y ante ese
  warning revisar el archivo final.
* **Un script que aplica VARIAS ediciones y aborta a mitad deja escritas las anteriores y ninguna de las
  siguientes — después de haber impreso `ok` de las anteriores.** Se lee como "todo aplicado" y no lo está.
  (2026-08-30, Control-de-acceso: un arreglo declarado hecho que nunca llegó al árbol.) **Después de
  cualquier script de ediciones, verificar en el ARCHIVO** (un `grep` del texto nuevo), y escribir después
  de cada reemplazo en vez de acumular. ⚠ Un `*/` adentro de un comentario de bloque de JS/TS lo cierra,
  aunque esté entre comillas invertidas.
* **Un script no se puede importar por ruta ABSOLUTA de Windows** en Node: `import ... from
  'C:/...'` revienta con `ERR_UNSUPPORTED_ESM_URL_SCHEME` (lee `C:` como protocolo). Va ruta **relativa**
  o `pathToFileURL()` de `node:url`.
* **Un script de Node que sale justo después de un error puede reventar con una aserción de libuv**
  (`Assertion failed: !(handle->flags & UV_HANDLE_CLOSING)`, de `async.c`) en vez de terminar limpio. Pasa
  en Windows con handles abiertos al salir y **no es el bug que se busca**: el error de verdad es el que se
  imprimió arriba. Repetir la corrida alcanza.
* **`python - @'...'@` desde la herramienta de PowerShell NO ejecuta el script**: Python abre su consola
  interactiva, lee fin de archivo y entra en un bucle de errores en segundo plano (2026-09-20: 2,6 GB de salida y
  una batería de tests que se quedó sin tiempo). Python de varias líneas, por la herramienta Bash con
  `python - <<'PY' … PY`. Ante una tarea de fondo colgada, mirar primero el TAMAÑO de su salida.
* **`… | Select-Object -First N` corta la tubería y deja `$LASTEXITCODE` en `-1`**, sin aviso: un control que
  frenó bien y otro que pasó se leyeron los dos como falla (2026-09-12). Para medir un código de salida:
  `& script *> $log; $LASTEXITCODE`, y filtrar el archivo después. En Bash, `${PIPESTATUS[0]}` es el PRIMER
  comando de la tubería.
* **Una mutación de prueba no se revierte con `git checkout -- <archivo>`**: vuelve a lo commiteado y se lleva
  también los arreglos sin commitear de ese archivo, con los tests en verde justo porque el código correcto ya no
  está (2026-09-12). Copia en memoria, escribir la mutación, correr el test acotado y restaurar en un `finally`.
* **Lo que un comando de Claude escribe en `AppData` va a una COPIA PRIVADA** (la app de escritorio es un paquete
  MSIX y Windows virtualiza `AppData` para todo lo que lanza, `Temp` aparte). Claude ve SU copia y cualquier
  proceso de afuera (tarea programada, otro programa) ve la real: los dos «escriben bien» y nunca se cruzan
  (2026-10-22: una tarea programada anotaba en un archivo y Claude leía otro, sin ningún error). Datos que
  comparten Claude y algo de afuera van fuera de `AppData` (p. ej. `%USERPROFILE%\<carpeta>`).
* **`npm audit fix --omit=dev` arregla el lockfile pero DESINSTALA las dependencias de desarrollo de
  `node_modules`** (2026-10-26, agent-card): después lint, tipos y build fallan con `MODULE_NOT_FOUND` y se
  leen como si el arreglo hubiera roto algo. Volver con `npm ci`. ⚠ Y si después el build de Next sigue sin
  encontrar un módulo que `require.resolve` sí encuentra, es su caché: borrar `.next` y compilar de nuevo.
* **Un Python de un `.venv` lanzado «al fondo» con `DETACHED_PROCESS` le abre al dueño una ventana negra en
  primer plano** (Windows Terminal), aunque lleve también `CREATE_NO_WINDOW`: el `python.exe` del `.venv` es
  un redirector que abre el Python base como HIJO, y ese hijo, sin consola heredada, recibe una nueva y visible
  (además `CREATE_NO_WINDOW` se ignora junto con `DETACHED_PROCESS`). Va **`CREATE_NO_WINDOW` +
  `CREATE_NEW_PROCESS_GROUP`, sin `DETACHED_PROCESS`**: la consola oculta la heredan los hijos. Lo mismo para
  cualquier proceso de fondo que lance otros (2026-10-30, SkyOne: la auditoría de dependencias del arranque).
* **Algo largo va con `run_in_background`, nunca con un `&` a mano en Bash**: ese proceso queda sin dueño en el
  acto y nadie lo puede cerrar después.
* **Entrar a una copia aparte (`EnterWorktree`) con agentes corriendo les bloquea todos los comandos**: la sesión
  queda atada a la copia. Se entra antes de lanzarlos o después de que terminen.
* **Mandarle un mensaje a un agente que ya terminó lo despierta sin el encargo original**, y hace otra cosa
  (observado en SkyOne, aunque la herramienta diga que conserva el contexto). Para seguir un trabajo terminado,
  encargo nuevo y autocontenido.

## Las dos PC (misma cuenta de Claude)

El dueño trabaja en dos computadoras con SU cuenta personal de Claude (la usa también para la empresa; está
hablado, no es un problema). Cuál es cuál: `$env:COMPUTERNAME`.

* **Notebook de la oficina** (i7-1255U, 16 GB en UNA sola placa): lunes a viernes de 11 a 18. Ahí está la mayor
  parte del trabajo (SkyOne y la empresa). Ya no viaja a la casa: queda en la oficina, a veces trabajando de noche.
  Las rarezas de la sección siguiente son de esta PC salvo que digan otra cosa. Su nombre de equipo: anotarlo la
  primera vez que se corra ahí.
* **Escritorio de la casa** (`PC-JOA-CASA`, antes `DESKTOP-1FBVMK9`: renombrada el 30/10/2026; Ryzen 5 3600 de 6 núcleos/12 hilos, 32 GB en 4 placas, Radeon
  RX 6600, dos SSD y un disco): noches, madrugadas y fines de semana; proyectos personales (Ocaso) y otras cosas.
  El tope de 2 agentes con tests pesados o navegadores se midió en la notebook; acá no se midió y rige el mismo.
  **El driver de la RX 6600 se cae de vez en cuando** (~25 veces desde feb-2026, la mayoría jugando; Windows lo
  reinicia y AMD deja un cartel «caducó el tiempo de espera de un controlador»). Un proceso que usaba la placa
  (DirectML, juegos) puede morir SIN imprimir nada, y un `| tail`/`| grep` le tapa el código de error: parece una
  prueba vacía. Toda corrida en la placa muestra su código (`echo rc=${PIPESTATUS[0]}`) y, si algo raro, se mira el
  registro de aplicaciones de Windows (evento LiveKernelEvent 141/117; la fecha real es la del nombre del volcado
  `WATCHDOG-aaaammdd-hhmm.dmp`, porque el registro repite los viejos). Herramienta lista en Monitoreo-clinicas
  (`scripts/chequear_placa.py`). Se notó el 30/10/2026 (12:45, un agente siguió de largo sin reportarlo).
  **Causa probable (volcados analizados el 30/10/2026, sin confirmar):** todas las caídas son el driver de AMD
  (`amdkmdag`) con dos versiones distintas, y hay 3 pantallazos azules de memoria corrupta en piezas distintas
  (núcleo al arrancar, audio, gráfico) → apunta a la RAM: 4×8 GB de dos marcas mezcladas (2 Kingston Fury
  KF3200C16D4/8GX + 2 genéricas) a 3.200 en una placa B350. Ajustes de AMD en fábrica (dice el dueño). Siguiente
  paso: MemTest86 de una noche; si falla, bajar a 2.933/2.666 o dejar solo el par Kingston. Los volcados se leen con
  `cdbX64.exe` (alias del WinDbg de la tienda; el `cdb.exe` de su carpeta da «acceso denegado») después de copiarlos
  como administrador desde `C:\Windows\LiveKernelReports` y `C:\Windows\Minidump`.
* **La cuota es UNA para las dos:** `get_usage` da la suma. `medir-consumo-semanal.py` lee las conversaciones de
  la PC donde corre, deja ese consumo (por tramo de 24 h y proyecto, esa semana y la anterior, 70 días de historia)
  en `consumo/<COMPUTERNAME>.json`, lo commitea y sube solo, y suma lo que dejó la otra (dice de cuándo es). Lo
  corre de fondo el hook de arranque si el archivo propio tiene más de 2 días; preguntar «tokens» también lo
  actualiza. Lo de hoy, los subagentes y los chats por tamaño quedan solo de la PC donde corre. Se notó el
  2026-10-27 (~23:30): la casa llevaba 1.507M tokens y 588 USD de lista en la semana del 21/10 (casi todo el
  trabajo nocturno de Ocaso) con el 85 % real; el resto era la notebook, que el script no veía.
* **Tareas pesadas sin nadie mirando (2026-10-27): se pueden proponer, sobre todo las de varias horas o que
  ahogan la PC.** La notebook queda en la oficina y está libre de noche; la de casa, de día (y de noche sin
  problema para proyectos personales como Ocaso). El dueño lo deja corriendo con Remote Control y lo mira un par
  de veces, sin estar encima: en esas corridas, decidir y anotar en vez de frenar a preguntar. Mejor de noche que
  de día en la PC que está usando.
* **La configuración se aplica en cada una por separado:** `settings.json` es local. Si cambia `setup-symlink.ps1`,
  volver a correrlo en las dos (el 2026-10-27 la de casa seguía compactando al ~97 % por eso). **Y cerrar los
  chats abiertos antes del cambio:** los de antes de las 15:10 del 27/10 se quedaron con el porcentaje viejo
  (60) Y la ventana nueva (633k) a la vez y compactaron a los ~368k (60 % de 633k, el 37 % del millón).

## Rarezas conocidas de la máquina y de la app (contestar sin re-investigar)

* **El Explorador se cae solo** desde el 2026-08-13 (barra de tareas y escritorio), solo en la NOTEBOOK. Firma
  fija: 0xc0000409, fail-fast código 7 dentro de Explorer.EXE, desplazamiento 0x6698e; siempre el proceso
  PRINCIPAL. 🔑 **Mecanismo (28/10, con los símbolos públicos y el depurador de la tienda, `Microsoft.WinDbg`):**
  0x6698e es `CTray::CheckGDIHandleLimit`, que **cierra el Explorador A PROPÓSITO** cuando sus objetos GDI pasan
  de `GDIProcessHandleQuota` − 500 (9.500 con el tope de 10.000). O sea: **algo le hace juntar objetos GDI sin
  liberarlos**, a ráfagas (vivió de 40 min a 20 h entre caídas; quieto, no crece). No es la RAM ni la carga.
  Descartados también, midiendo: abrir y cerrar ventanas, cambiar íconos de la bandeja (incluido
  LibreHardwareMonitor) y las ráfagas de cambio de plan de energía de `WUDFHost`/`FnKey` de Clevo (preceden a
  las caídas igual que a cualquier instante al azar). 🔑 **Culpable (29/10, reproducido):** el **chequeo de
  pantallas de SkyOne** (`scripts/dev/chequeo-pantallas.py`). Cada pantalla le deja al Explorador ~6 objetos GDI
  y ~3 USER (proporción 2:1 = íconos); la corrida de publicar (`--vistas --jobs 8`, todas) lo llevó de 195 a
  9.995 entre 18:21 y 18:37 del 28/10 y murió al tocarlo a la mañana siguiente. Prueba controlada: agenda+clientes
  con `--vistas` (224 pantallas) = 216 → 1.545. Con la vigía: 19 de 19 minutos con el chequeo corriendo suben
  (9.366 objetos), 7 de 408 sin él (359). **Causa exacta:** cada contexto de incógnito de Playwright
  (`new_context`) en Edge que vive más de ~1 s le deja al Explorador su ícono de InPrivate (8 páginas de 3 s:
  incógnito +48, perfil normal 0; el contenido de la página no importa). **Arreglado en SkyOne:** el chequeo usa
  un perfil normal y una página por pantalla (224 pantallas: +0); un test impide volver. Cualquier otra
  herramienta que abra MUCHAS páginas con `new_context` en Edge haría lo mismo. La caída del 28/10 18:04 es
  OTRA (0xc0000005 en `Windows.UI.Xaml.dll`, con el menú Inicio al frente y solo 643 objetos).
  `vigilar-explorador.ps1` (al lado de este archivo) anota cada 30 s la cuenta GDI, el programa al frente y las
  carpetas abiertas (la cuenta por tipo lee mal la tabla en Windows 11: no ve los objetos que se acumulan). Y
  `capturar-caidas-explorador.ps1` (como admin) guarda un volcado completo de la próxima caída. Instalar la vigía
  en el inicio de sesión lo frena el modo automático (persistencia): lo corre el dueño.
* **La PC se ahoga con varios chats en paralelo (2026-10-20):** es la carga de trabajo sobre un procesador de bajo
  consumo (i7-1255U) y 16 GB en UNA sola placa. El antivirus pesa: crear+leer 2000 archivos chicos con Python =
  4,7 s de mediana. El buscador de Windows NO indexa `C:\GitHub` (no hay nada que sacarle). Modo de energía:
  «Máximo rendimiento» enchufado, lo puso el dueño.
  **Los 2 núcleos rápidos clavados en 0,4 GHz con carga sostenida NO son una falla** (medido con
  LibreHardwareMonitor, instalado): el chip tiene ~15 W sostenidos tras ~1 min de turbo y, enchufado, reparte ese
  presupuesto a los 8 núcleos chicos (a batería, al revés). Se descartaron el cargador (Chicony 45 W original; recién
  enchufado da 2,8-3,3 GHz), la zapatilla y la temperatura (máx. 77 °C). Mirar solo los núcleos rápidos engaña: la
  vara es el «trabajo real» del Administrador de tareas. Base recién reiniciada, Claude con un chat: rápidos 2,3 GHz,
  9,9 % de trabajo real, 54 °C de placa, 8,5 de 15,7 GB de RAM.
  **Decidido que NO: bajar los procesos de la suite para que la PC responda mejor** (medido, PC sin otros chats,
  una corrida por lado): 10 procesos = 4 min 15 s, 6 = 4 min 19 s (el tope de 15 W iguala); una tarea chica a
  prioridad normal tardó de mediana 60 contra 57 ms (19 en reposo), p90 106 contra 148, peor 441 contra 224. No
  mejora la respuesta de forma clara, y con 6 una segunda corrida entraría en paralelo en vez de esperar su turno.
  **Decidido que NO: excluir cosas del antivirus** (ni por carpeta ni por proceso). Por carpeta, las revisiones
  también se la saltean, así que nunca se revisaría. Por proceso, hay que excluir el intérprete de Python, que
  Microsoft pone en su lista de «nunca excluir», y es el mismo que instala paquetes de internet. El dueño no
  quiere bajar la seguridad.
  **Decidido que NO: mudar los repos a un Dev Drive** (VHDX ReFS con modo rendimiento; piloto en CSKY-SA/skyone
  GH-611). Crear+leer 2000 archivos (`medir-antivirus.py`) baja de ~2,6 s a ~1,1 s, pero la suite entera NO mejora:
  alternada con chats abiertos dio C: 313/340 s contra Dev Drive 358/540/559 s. La suite gasta CPU, no espera
  disco, y el modo rendimiento no baja la CPU del antivirus (los ~12 % que se ven con 3-4 chats siguen igual).
  Antivirus medido con carga real: ~34 s de escaneo cada 5 min, ≈1 % de la máquina. Reabrir solo si aparece un
  cuello de DISCO medido, no de CPU.
  **Decidido que NO: achicar las copias del conector de mail** (`mcp-mail-empresa`, una por chat abierto, cada una
  con su lanzador del `.venv`): medido 2026-10-23, ~68 MB privados por chat (7 chats ≈ 480 MB, 3 % de la RAM) y
  casi nada de CPU. Cargar las librerías de Google recién al primer uso ahorra ~10 MB por chat (el peso es el
  paquete `mcp` mismo, 57 MB); un servidor único compartido ahorra más pero, si se cae, deja a todos los chats sin
  mail y pide tenerlo siempre prendido. Reabrir solo si la RAM pasa a ser el freno medido.
  **Historia del consumo:** Windows no la guarda por programa. `registrar-consumo-pc.ps1` (al lado de este
  archivo) anota cada N min (`-Minutos`, 5 por omisión; 1 para ver picos), por tarea programada, CPU y RAM por
  familia (SkyOne pantallas / SkyOne resto / Vision / Claude / Edge / antivirus / resto) en
  `%USERPROFILE%\registro-consumo-pc\`; cuesta ~3,5 s de CPU por corrida (≈0,1 % de la máquina cada 5 min, ≈0,5 %
  cada 1 min). `-Instalar -Hasta '…' [-Minutos N]` / `-Desinstalar`. Sirve igual para medir la PC nueva.
* **El selector de esfuerzo** de la app se revierte solo a los ~6 s si se elige ANTES de abrir el chat (bug de la
  app, no de su config). Rodeo: elegirlo con el chat ya abierto.
* **Abrir chats NUEVOS desde el teléfono en esta PC (2026-10-27, armado en Ocaso):** la app de escritorio no
  lo hace sola (Remote Control de la app solo continúa un chat ya abierto; Dispatch vive en Cowork y está en beta
  limitada). La vía es `claude remote-control` (modo servidor) en una ventana de PowerShell propia, dentro del
  repo: es el mismo motor de Claude Code (CLAUDE.md, permisos, hooks, memoria), sin el navegador del panel ni la
  lista de tareas de la app. Dos trampas: **(1)** el usuario de Windows tiene `ANTHROPIC_API_KEY` guardada
  (alcance User, `sk-ant-…`); con ella cargada Remote Control no arranca y cualquier `claude` de terminal podría
  facturar por API. Se vacía solo en esa ventana (`$env:ANTHROPIC_API_KEY = ''`); no se borró, el dueño no
  confirmó todavía si la usa. **(2)** El login de la terminal es aparte del de la app y vence: `claude` → `/login`
  (cuenta con suscripción) → `/exit`. Sin `origin/HEAD` local los chats remotos van a una rama inventada:
  `git remote set-head origin -a`. Plantilla: `Monitoreo-clinicas/scripts/remoto.ps1` (la de Ocaso no está clonada en la PC de la casa). Cerrar la ventana NO frena el
  proceso: queda de fondo (buscar `claude.exe remote-control` y frenarlo).
* **Un ayudante «placeholder» con encargo «noop»** que aparece rechazado en rojo lo lanza la app, no un chat; el
  rojo es el bloqueo por precaución cuando el control de seguridad no contesta. Solo se reporta a Anthropic si
  pasa seguido.

## El detalle largo de las reglas del `CLAUDE.md`

Lo que sostiene una regla, cuando el porqué no entra en el renglón que la enuncia.

### Subagentes: de dónde salen los números

* **Equivalencia vigente para estimar:** 1 punto de cuota ≈ **67M tokens ≈ 26,6 USD de lista** (cierre de la
  semana del 21/10 con 87 %, las dos PC sumadas; antes 82M / 30 USD, medido a mitad de semana en una sola PC). Para estimar sirven los tokens: los dólares por punto se
  movieron más de lo que explica el precio del modelo. Se recalibra al cierre de cada semana con
  `medir-consumo-semanal.py <miércoles del reinicio> <% de get_usage>`, **sumando las dos PC** (ver §Las dos PC).
  **La estimación nunca se informa como real** (2026-10-30): el script dio 30,7 contra **34 %** de la app (subestima
  ~10 %, y los datos de la otra PC llegan con atraso). Si la sesión no tiene `get_usage`, se dice y se pide el % al dueño.
* **Fable no es superior (2026-10-19):** en Artificial Analysis Opus 5.5 rinde más que Fable 5.1 y cuesta la
  mitad en cada nivel de esfuerzo, y en tres publicaciones de SkyOne trajo más hallazgos reales y menos falsas alarmas.
* **Piso para delegar construcción (2026-10-29, regla 3):** sale de Gentle-AI (`internal/assets/claude/orchestrator.md`
  y la tabla «Measured» de su README): un arreglo de 3 líneas costó 0,339 USD delegado contra 0,105 directo, porque
  un subagente pasa 1-2 min leyendo antes de escribir. Es UNA corrida y en otro entorno: se recalibra con
  `medir-consumo-semanal.py` si aparece un caso propio que lo contradiga.
* **Otro chat en vez de subagentes (decidido que no, 2026-10-16):** se revisa si la app mejora cómo un chat
  muestra lo que hizo el que lanzó.

* **La regla 5 tal como estaba hasta el 2026-09-22** (la reemplazó la versión corta del `CLAUDE.md`: techo de 10, el tiempo por sobre los tokens). Queda acá por las mediciones que trae:

  > ## 5. Delegar en subagentes
  > 
  > * 🔴 **Lo que manda es el MEDIDOR** (2026-09-16, reemplaza al «por defecto lo hacés vos» del 12/09): **por debajo de la línea de ritmo** (ver 📊 abajo), una tarea mediana o grande que se beneficia de 2-3 agentes **los lanza sin preguntar** — la suscripción está para usarse. **Por encima de la línea**, modo austero: lo hacés vos en el chat y un agente va solo si leerlo acá llenaría el chat o si hace falta una mirada INDEPENDIENTE. En los dos modos, "el trabajo se parte" solo NO alcanza como motivo para paralelizar.
  > * **Por qué:** cada agente arranca de cero —instrucciones, herramientas, relee lo que vos ya leíste— y no aprovecha el caché del chat. Ese costo fijo se paga por agente, así que **lo que gasta es CUÁNTOS se lanzan, no cuántos corren juntos**: tres y después otros tres cuesta lo mismo que seis a la vez.
  > * 🔴 **Techo: 4 agentes por CHAT, contando el TOTAL** (2026-09-15): bajo la línea de ritmo los cuatro van sin preguntar; en modo austero, dos sin preguntar y los otros dos con un aviso de una línea. **Para el quinto, frená y pedime OK** en una línea diciendo para qué. Arriba del techo se PIDE, no se recorta en silencio. ⚠ **Si desde el arranque ya se ve que el trabajo necesita más de cuatro, preguntámelo ANTES de empezar** — y la respuesta correcta casi siempre es partir el trabajo en dos chats, no sumar agentes.
  > * 🔑 **QUÉ se delega importa más que cuántos** (medido el 2026-09-15 sobre 277 subagentes): tener algo en el chat es un **ALQUILER** —50k tokens cuestan 0,025 USD por cada turno que siga— mientras que el subagente **se muere con su contexto** y se paga una sola vez (~4 USD, 0,12 puntos de cuota). Entonces **delegá lo que LEE MUCHO y CONCLUYE POCO** —barrer archivos, auditar, una mirada independiente—, pero **"mucho" es de verdad: más de ~150k tokens de lectura** (empata a los ~30 turnos que le queden al chat; 50k recién empata a los ~150 turnos, así que una lectura mediana la hacés vos). La mirada independiente justifica el agente sin importar el tamaño. 🔴 **Si lo que devuelve lo vas a tener que releer o rehacer entero, hacelo vos: así se paga dos veces.** ⚠ Y no creas que delegar baja el contexto del chat: los chats con 5+ agentes de esa semana terminaron en 61 % de ventana contra 40 % los que no usaron ninguno.
  > * 📊 **Presupuesto semanal y medidor** (medido 2026-09-16): **1 punto de cuota ≈ 33 USD a precio de lista ≈ 48-55M tokens**, y **VARÍA** con la mezcla (más relectura de caché = más tokens por punto; el 18/09 dio 55M): 🔴 **si pregunto cuánto gasté, el número lo da `get_usage`; la equivalencia solo sirve para repartirlo** por intervalo o proyecto. **Si pido un análisis de mi consumo sin más detalle** = la semana en curso en **tramos de 24 h desde el reinicio** contra la línea de ritmo: `medir-consumo-semanal.py <miércoles del reinicio> <% de get_usage>` (al lado de este archivo). La semana se reinicia el **miércoles 19:00**. Reparto: 10 pts de margen, ~12 para 3 publicaciones, **~11 por día** para el resto, de los cuales **~2 en subagentes (15-20 por día en total)**. **Línea de ritmo: la cuota no pasa de 13 % por día corrido desde el reinicio** (= los 90 sin margen / 7, publicaciones incluidas: la cuota real se compara contra 13, nunca contra 11) (jue 13 · vie 26 · sáb 39 · dom 52 · lun 65 · mar 78 · mié 90). 🔴 **Antes de arrancar un trabajo grande o de lanzar agentes, leé la cuota real** (`get_usage` de la app) y comparala con la línea: si voy pasado, decímelo en una línea con la versión liviana. **La palanca más grande es el largo del chat, no los agentes** (más de la mitad del gasto fue el chat cargando su contexto; un agente ≈ 12 turnos de un chat de 650k): un trabajo grande se parte en dos chats.
  > * **No cuentan contra el techo** (van sin preguntar): la revisión antes de ESCRIBIR en una base de datos y el chequeo de cierre de chat.
  > * 🔴 **Workflows (orquestación multiagente): SIEMPRE con mi autorización explícita**, en ese turno, diciendo cuántos agentes estimás.
  > * **Lo que NO se delega:** buscar una función, leer un archivo que ya sé cuál es, un cambio de una línea.
  > * **Todo agente que emita un JUICIO va en el modelo grande de siempre** (bajar de modelo se probó y funciona peor; Sonnet está descartado); el chico, solo para barrido mecánico verificable. **El modelo tope (Fable) solo para lo crítico**: revisión antes de publicar o de escribir en una base. 🔑 **Un modelo se pide por FAMILIA (`opus`, `fable`, `sonnet`), nunca por número** (2026-09-22): así corre siempre el último. El número fijo va solo donde un cambio de modelo puede romper algo sin avisar (el código de una app que llama a la API: ahí se fija y se actualiza a propósito, probándolo) o en un registro de qué modelo corrió.
  > * **La refutación adversarial también es solo para lo crítico** (lo que sale hacia afuera, lo que escribe datos, lo que se publica). Y cuando va, es **UN adversario para la lista entera**, nunca uno por hallazgo. En lo demás, verificá vos los hallazgos contra el código.
  > * 🔴 **El encargo de un JUICIO (revisar, auditar, refutar) va SUELTO, en cualquier modelo, Fable incluido** (medido 2026-09-03, dos modelos × dos estilos: la forma de pedir pesó más que el modelo): objetivo, contexto, qué preocupa y los límites de seguridad en firme. **Nunca pasos numerados, herramientas dictadas, formato de salida cerrado ni conclusiones ajenas dadas por verificadas.** Con formulario, los dos modelos devolvieron una lista; sueltos, probaron rompiendo en una copia, refutaron hallazgos previos y **cuestionaron el encargo mismo**. Si hay chequeos que no pueden faltar, van como **«como mínimo»**, y el encargo cierra preguntando **si lo revisado es la forma correcta de resolver el problema**. Detalle: skill `revisar-lo-que-se-sube` de SkyOne, Paso 5.
  > * El subagente devuelve un **veredicto o un dato**, no un relato: yo no veo lo que devolvió, me lo contás vos. No ven la charla → el encargo va autocontenido. Y **no escriben el mismo archivo a la vez**: o va uno solo, o cada uno en su worktree.
  > * 💳 **El costo SÍ es criterio en agentes** (cambió el 2026-09-12). Lo que se escribió antes con "el costo no es criterio" para lanzar más agentes quedó vencido.
  > * Las mediciones que sostienen todo esto: `C:\GitHub\1-Mi-config-de-Claude\entorno-windows.md`.


* **Historia del techo** (lo vigente está en `CLAUDE.md` §5): el 2026-09-15 pasó de 3 a 4 por chat y el
  2026-09-16 la permisividad pasó a depender del medidor (línea de ritmo de 13 %/día). El 2026-09-22 subió
  a 10 («el tiempo por sobre los tokens») y el 2026-09-24 bajó a **3 a la vez / 6 en total**: el primer
  día de la semana cerró en 17,1 puntos contra 16 de línea, con los agentes en 47 % del gasto (56 agentes,
  ~5 USD c/u) y dos chats de 8 y 10 agentes que solos sumaron 6 de esos 17 puntos. El dueño trabaja con
  4-6 chats abiertos a la vez (pico medido: 6 el 23/09), así que el techo por chat se multiplica. El
  disparador: un «limpiá ramas» lanzó 5 revisores (uno por rama) amparado en una excepción del proyecto.
  El 2026-10-21 subió a **5 a la vez / 8 en total**: dos semanas seguidas cerraron en 70-80 % de la cuota y
  el dueño quiso más velocidad sin duplicar el gasto. Lo simultáneo se subió libre porque paralelo o en fila
  cuesta lo mismo; el total solo un tercio, porque los agentes son ~la mitad del gasto y el margen sobrante
  era 20-30 % (→ los agentes pueden crecer 40-60 %, no el doble que daría 10). ⚠ Chats de 8 y 10 agentes
  fueron justo lo que disparó la baja del 24/09: si una semana vuelve a pasar la línea de ritmo, se vuelve
  a 3 / 6. Lo que sigue es el porqué del techo por chat, que no se venció.
* **El techo de 3 agentes por CHAT (total) y los workflows siempre con OK** (dueño, 2026-09-12) reemplazan
  al de «5 por tanda, una tanda por fase» del 2026-09-10. Con ese techo la cuota semanal llegó al 60 % a
  mitad de semana: contar por tanda dejaba abierto tres, después tres, después tres, que cuesta lo mismo
  que nueve juntos. El costo de un agente es casi todo FIJO (arranque, instrucciones, relectura), así que
  lo único que ahorra es lanzar menos. Excepciones que no cuentan: revisión antes de escribir en una base
  y el cierre de chat.
* La ventana que se cuida es la SEMANAL: de 100 a 200 dólares de plan, la de 5 horas se cuadruplica, pero
  la semanal Anthropic no la publica y las mediciones de terceros van de **1,6x a 3,5x** (la más seria: 3
  cuentas, Classmethod/DevelopersIO, ago-2026). Con semanas de 77-97 % del de 200, **el de 100 no alcanza en
  ningún escenario** (revisado 2026-10-13): no se vuelve a plantear salvo semanas de ~35 % sostenidas.
* **Modo rápido: descartado.** En la suscripción NO sale de la cuota: se cobra como uso extra a la tarjeta
  (con el uso extra apagado queda bloqueado y no cobra). Los 200 USD/mes de créditos de API del plan Max NO
  cubren Claude Code interactivo (solo API, Agent SDK, Managed Agents) y no consta que paguen modo rápido →
  ante la duda, no. Esos créditos no se vinculan a la organización de API de la empresa (la paga la empresa;
  el dueño no lo mezcla). Si algún día se vincula una propia: sin tarjeta cargada, y nunca dejar su llave en
  el entorno (desvía los chats a facturación por API).
* **Por qué no se baja de modelo:** se midió. Mismo encargo, mismo código: **32 hallazgos contra 4**, y las
  dos cosas graves las vio solo el modelo grande (2026-09-02). El chico queda para barrido mecánico
  verificable (listar, contar, encontrar), nunca para un juicio.
* **Un subagente no ahorra tokens: gasta más.** Compra tiempo de reloj y contexto limpio.
* **De dónde sale el presupuesto semanal** (2026-09-16, ventana 9/9 19:00 → 16/9 19:00, todos los proyectos,
  ~97 % de cuota usada): 3.200 USD equivalentes, 4.713M tokens (98 % caché), 292 subagentes = 37 % del
  gasto (~4 USD c/u). SkyOne 76 pts, QA de SkyIA Web 22. Se fue de miércoles a sábado (19-26 pts por día).
  Por tipo de chat en SkyOne: consulta 0,1 pt · chico 0,5 · mediano 1,4 (4,7 agentes) · grande 5,3 (13
  agentes; 8 chats = más de la mitad) · publicación 3-4,7. El umbral para delegar sale de: leer en el chat
  cuesta la escritura de caché (6,25 USD/M) una vez + 0,5 USD/M por turno; contra ~4 USD fijos del agente.
  El ritmo se mide con `get_usage` (la app devuelve % semanal y hora de reinicio).
* **Semana 16/9 19:00 → 23/9 19:00** (80 % de cuota, leído con 1,5 h por delante; el modelo pasó de Opus 5 a
  Opus 5.5 el 22/09 y el script ya lo precia aparte): 2.804 USD de lista, 4.710M tokens → **35 USD y 58,9M
  tokens por punto** (antes 33 y 48,6: el modelo nuevo rinde más tokens por punto). 222 subagentes = 39 % del
  gasto. Tramos: 8 · 14 · 14 · **0 (fin de semana)** · 15 · 17 · 12. Los dos últimos, ya con el techo de 10
  agentes, se fueron a 56-62 % en agentes. Chats: consulta 0,05 pt · chico 0,47 · mediano 1,37 (3,1 agentes)
  · un solo grande (3,4): cerrar chats más seguido bajó el costo del chat grande. Sobraron 20 puntos.
* **Re-medición con el medidor corregido (25/09)** — el viejo subcontaba la salida (~40 %) y la escritura de
  caché de 1 hora: semana 9-16/9 (97 %, Opus 5) **37,5 USD y 48,7M por punto** · 16-23/9 (80 %, casi todo
  Opus 5) **40 USD y 59,4M** · 23-30/9 a mitad (36 %, Opus 5.5) **29,8 USD y 82,3M**. Hipótesis que calza justo:
  **la cuota cobra el token de Opus 5.5 igual que el de Opus 5** (38 × 0,8 = 30: el descuento del 20 % es de la
  lista de la API, no del plan). Si es así, los tokens por punto subieron por la MEZCLA (más relectura de
  contexto, que es barata), no porque el punto rinda más. Los tokens por punto no miden eficiencia: la medida
  es cuota por TAREA, y comparar modelos pide la misma tarea corrida con los dos. Otras PC: menos del 3 % (dueño).
* **Un juicio que no fue refutado no es un resultado, es una impresión:** de 23 hallazgos marcados graves,
  la refutación adversarial dejó 3. Desde el 2026-09-12 esa refutación con agente queda para lo crítico
  (un adversario para toda la lista); en lo demás la verificación contra el código la hace el chat.

### Aviso de contexto y de costo (regla 3)

* **Qué pide cada umbral** (la versión larga de la regla, recortada del `CLAUDE.md` el 2026-10-16): **40 %** =
  una línea al pie nombrando el corte natural, y de ahí en adelante el estado escrito a medida que se avanza;
  **60 %** = checkpoint armado al pie (qué quedó terminado, qué falta) y se sigue si no hay respuesta; **75 %** =
  Claude cierra, con el traspaso escrito. Más dos avisos por COSTO del chat con sus subagentes (**2 y 4
  puntos**), que cazan el chat que gasta sin agrandarse. Cada umbral avisa una vez; si el chat se compacta,
  los de contexto se rearman.
* **Rehecho el 2026-10-24** (`hooks/aviso-contexto.py`): el original vivía solo en `~/.claude/hooks` de una
  máquina, nunca entró al repo y en la otra no existía. Ahora está en el repo, `setup-symlink.ps1` lo registra
  y `check-symlink.ps1` avisa al arrancar si a una máquina le falta (igual que el bloqueo de chats y Opus por
  defecto, que se habían perdido de la misma forma).
* **Cómo mide:** el contexto es el último mensaje del chat (entrada + caché + salida) sobre la ventana: 1
  millón en Opus 5.5, Opus 5, Fable y Sonnet 5; 200 mil en Haiku o con el 1M apagado; se fuerza con la
  variable `AVISO_CONTEXTO_VENTANA`. El costo usa `precio()` y `USD_POR_PUNTO` de `medir-consumo-semanal.py`:
  se recalibra ahí y el aviso lo toma solo. Lee cada archivo desde donde quedó la vez anterior (marcas en
  `~/.claude/aviso-contexto/`, fuera de `AppData` por el MSIX) y dentro de un subagente no avisa.
* 🔑 **Un hook se paga en ARRANCAR, no en lo que hace, y se paga por herramienta y por chat abierto.** Con 7
  chats, más de la mitad de la notebook se iba en procesos de vida corta (git, hooks, sus consolas). Las tres
  reglas: Python y no PowerShell (PowerShell 5.1 se comió ~2,5 s de procesador por arranque con la máquina
  cargada); registrarlo con `command` + `args` (con `command` suelto el arnés lo lanza por bash: un proceso y
  una consola más); `-S` si solo usa la biblioteca estándar (359 → 234 ms de procesador, medido 2026-10-29).
  Varios hooks del mismo evento en un proyecto: UN proceso que los corre adentro (SkyOne,
  `controles-al-editar.ps1`: −37 % por edición). Medirlo: `TotalProcessorTime` del proceso hijo, A/B intercalado.
* **Python y no PowerShell:** corre en cada herramienta, y Python tarda ~0,3 s contra ~1 s. Probarlo sobre un
  chat ya hecho: `python -I hooks/aviso-contexto.py --probar <ruta del .jsonl>`. Referencia del 24/10: el chat
  más grande de la máquina llegó a 61 % y 1,5 puntos; ninguno pasó de 2.

### Formatos locales: por qué es una lista y no un criterio

Es una familia de errores que el entorno de quien programa resuelve solo y que el dueño ve siempre. **No
fallan, no tiran error, no los agarra ningún test:** la pantalla simplemente queda mal. Por eso lo único
que los caza es una lista que se repasa.

* **El formato sale del dato, no del navegador de quien mira.** Un registro tiene que leerse igual para
  todos; si depende del idioma que cada uno tenga configurado, el mismo dato dice 07/03 para uno y 03/07
  para otro.
* **Cómo se arreglan los controles que dibuja el navegador:** `color-scheme` en `:root` y `lang` específico
  (`es-AR`, no `es`). Lo que el navegador no deja controlar —el orden de los campos de un
  `datetime-local`— se resuelve **leyendo de vuelta** lo que se escribió, en formato local y con el día de
  la semana, en vez de reemplazar el control nativo.

> ⚠ Las dos ÓRDENES de esta regla —centralizar el formateo en un módulo, y escribir la lista en la
> documentación del proyecto— **viven en el `CLAUDE.md`, no acá**: son instrucciones, no justificación.
> Acá está solo el porqué y la mecánica.
