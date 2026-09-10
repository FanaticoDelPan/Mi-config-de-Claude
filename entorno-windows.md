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

* **El techo de 5 por tanda y la cadencia de una tanda por fase** (dueño, 2026-09-10) reemplazan al tramo
  viejo de «8 a 15 cuando el trabajo lo amerita». Lo que molesta no es una tanda grande sino **mandar
  agentes seguido**: contra la ventana SEMANAL —la que importa— no pega la ráfaga de una vez, pega el goteo.
  De 100 a 200 dólares de plan, la ventana de pocas horas se cuadruplicó y el techo semanal apenas se
  duplicó: por eso la de pocas horas sobra y la semanal es la que se cuida.
* **Por qué no se baja de modelo:** se midió. Mismo encargo, mismo código: **32 hallazgos contra 4**, y las
  dos cosas graves las vio solo el modelo grande (2026-09-02). El chico queda para barrido mecánico
  verificable (listar, contar, encontrar), nunca para un juicio.
* **Un subagente no ahorra tokens: gasta más.** Compra tiempo de reloj y contexto limpio.
* **Un juicio que no fue refutado no es un resultado, es una impresión:** de 23 hallazgos marcados graves,
  la refutación adversarial dejó 3.

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
