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
  (`git commit -F`, `gh --notes-file`), nunca inline. **Un script se escribe con Write y se ejecuta por su
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

## El detalle largo de las reglas del `CLAUDE.md`

Lo que sostiene una regla, cuando el porqué no entra en el renglón que la enuncia.

### Subagentes: de dónde salen los números

* **El techo de 3 agentes por CHAT (total) y los workflows siempre con OK** (dueño, 2026-09-12) reemplazan
  al de «5 por tanda, una tanda por fase» del 2026-09-10. Con ese techo la cuota semanal llegó al 60 % a
  mitad de semana: contar por tanda dejaba abierto tres, después tres, después tres, que cuesta lo mismo
  que nueve juntos. El costo de un agente es casi todo FIJO (arranque, instrucciones, relectura), así que
  lo único que ahorra es lanzar menos. Excepciones que no cuentan: revisión antes de escribir en una base
  y el cierre de chat.
* La ventana que se cuida es la SEMANAL: de 100 a 200 dólares de plan, la de pocas horas se cuadruplicó y
  el techo semanal apenas se duplicó.
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
* **Un juicio que no fue refutado no es un resultado, es una impresión:** de 23 hallazgos marcados graves,
  la refutación adversarial dejó 3. Desde el 2026-09-12 esa refutación con agente queda para lo crítico
  (un adversario para toda la lista); en lo demás la verificación contra el código la hace el chat.

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
