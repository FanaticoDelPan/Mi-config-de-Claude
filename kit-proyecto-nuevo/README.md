# Kit para arrancar un proyecto nuevo

> **Qué contesta:** qué se pone en un repo nuevo del dueño el día 1, qué se agrega después y con qué gatillo,
> y qué NO se copia. Destilado del proyecto principal del dueño y filtrado por una revisión adversarial con la
> vara «¿es sobre-ingeniería para un repo con cero usuarios?». **Está escrito para el Claude que arranque ese
> proyecto**, no para el dueño.
>
> **Nada de esto es de un producto.** Ni nombres de herramientas, ni de personas, ni de tablas. Si aparece uno,
> es un bug del kit (el paso 3 de §Cómo se actualiza lo busca).

## Las tres capas de lo aprendido (y por qué el kit es solo una)

| Capa | Dónde vive | Qué va |
|---|---|---|
| **Global** | `CLAUDE.md` de este repo (se carga en TODOS los chats de todos los proyectos) | Lo que cambia lo que hago en cualquier chat: cómo le hablo al dueño, subagentes, cierre de chat, git, validar. **No se repite acá ni en la semilla**: rige solo. |
| **Kit** | esta carpeta | Lo de una sola vez: lo que se pone el día 1 y lo que se agrega al cumplirse un gatillo. Se copia al repo nuevo y desde ahí es de ese repo. |
| **Proyecto** | el `CLAUDE.md`, `docs/` y `.claude/` de cada repo | Lo que depende del producto, del server o de las personas. |

🔑 **Una lección de método que aparece trabajando en cualquier proyecto y vale para todos va a la capa que le
toca EN EL MISMO TRABAJO** (lo manda el `CLAUDE.md` global). Es el mecanismo que mantiene esto vivo: la foto
anterior de este kit quedó vieja en seis semanas sin que nada avisara, porque dependía de que alguien pidiera
«actualizalo». La vía incremental la cuida un control al commitear en este repo (`.githooks/pre-commit`):
frena si se cuela un nombre de producto, persona o cliente en el kit, o si el `CLAUDE.md` global pasa su tope.

## Cómo se usa (en el proyecto nuevo)

1. `CLAUDE-semilla.md` → `CLAUDE.md` en la raíz, completando los `<…>`. **Techo 15 KB, con control que falla
   desde el primer commit** (`escalar-el-arnes.md` §Presupuesto de peso).
2. `dia-1.md` → a `docs/`; aplicar lo que corresponde al **tipo de proyecto** (su primera sección) **antes de
   la primera pantalla**, con un ticket por innegociable.
3. `reglas-por-area.md` → cada área que el proyecto tenga, a su `docs/reglas-<área>.md`, con un puntero en el
   `CLAUDE.md`.
4. `skills/commitear` → a `.claude/skills/` del repo. `skills/cerrar-chat`, **recién cuando el proyecto tenga
   pasos de cierre propios** (tickets, novedades); hasta entonces alcanza el §12 del `CLAUDE.md` global. Van
   por proyecto y no globales a propósito: un skill personal le gana a uno del proyecto con el mismo nombre.
5. `agente-revisor-final.md` → a `.claude/agents/revisor-final.md` **recién con la primera publicación con
   usuarios**, ajustando los ángulos y las reglas duras.
6. `ci-ejemplo.yml` → `.github/workflows/ci.yml`, adaptado al stack.
7. `patrones-de-control.md` y `checklist-pantalla.md` → a `docs/`, citados desde el `CLAUDE.md`.
8. `escalar-el-arnes.md` y `lo-que-no-se-lleva.md` → a `docs/`: son la lista de lo que **todavía no** se hace.
9. `chequear_gatillos.py` y `test_chequear_gatillos.py` → a `scripts/`, enganchados al pre-commit (aviso) y a
   la CI (el test, y el chequeo con `--estricto`; `ci-ejemplo.yml` ya trae los dos pasos). Es lo que avisa
   cuando un gatillo de `escalar-el-arnes.md` se cumple.
10. `conectar-herramientas.md` → a `docs/` **recién cuando el proyecto se conecta a un sistema que no es suyo**
    (el chequeo de gatillos lo avisa si aparece una credencial externa).

## En un repo que ya existe

El kit no se copia entero sobre un repo vivo. Lo que sí se aplica, con su gatillo:

- **El `CLAUDE.md` pasa el techo** → tope duro con control y partir (el detalle a su doc, queda el puntero).
  Es lo primero: un `CLAUDE.md` de 40-60 KB se paga en cada chat.
- **El estado vive en prosa** (pendientes, avances en docs) → a tickets, y se borra de la prosa.
- **El cierre de chat usa subagentes o tarda más de 2-3 turnos** → el §12 del global, o `skills/cerrar-chat`.
- **El chequeo de gatillos** entra a cualquier repo vivo, con `escalar-el-arnes.md` a su `docs/` (es su lista).
  Si el repo ya tenía su propia lista de piezas faltantes, esa lista apunta a la del kit para lo genérico y se
  queda solo con lo suyo. En la primera corrida avisa todo lo que ya se cumplió, y cada aviso se resuelve una
  vez en `docs/gatillos.json`.
- El resto, solo cuando su gatillo de `escalar-el-arnes.md` se cumple en ese repo.

## Los archivos

| Archivo | Para qué |
|---|---|
| [`CLAUDE-semilla.md`](CLAUDE-semilla.md) | Las reglas duras del día 1 y dónde va cada cosa que se quiere dejar escrita. |
| [`dia-1.md`](dia-1.md) | Los innegociables antes de la primera pantalla, según el tipo de proyecto, con el motivo de cada uno. |
| [`reglas-por-area.md`](reglas-por-area.md) | Las reglas duras de cada área de un producto (datos, errores, listas, interfaz, IA, publicación). |
| [`patrones-de-control.md`](patrones-de-control.md) | Cómo se escribe un control que no se pudre, y cuándo uno deja de rendir. |
| [`checklist-pantalla.md`](checklist-pantalla.md) | Los errores de interfaz que no fallan, no tiran excepción y ningún test agarra. |
| [`agente-revisor-final.md`](agente-revisor-final.md) | El revisor adversarial antes de publicar: rol, herramientas recortadas, ángulos fijos, vueltas. |
| [`ci-ejemplo.yml`](ci-ejemplo.yml) | El pipeline mínimo del primer commit. |
| [`skills/`](skills/) | `cerrar-chat` (liviano, sin subagentes) y `commitear` (solo lo del chat), como plantillas. |
| [`escalar-el-arnes.md`](escalar-el-arnes.md) | Qué se agrega **después**, con el gatillo concreto. Existe para que no se copie todo el día 1. |
| [`chequear_gatillos.py`](chequear_gatillos.py) | Avisa los gatillos de `escalar-el-arnes.md` que ya se cumplieron sin decisión. Su test fabrica cada señal y verifica que la siga cazando. |
| [`conectar-herramientas.md`](conectar-herramientas.md) | Cómo se conecta a un sistema de otro: la vía menos peligrosa, solo lectura de entrada, y una prueba que demuestra que escribir falla por permiso. |
| [`lo-que-no-se-lleva.md`](lo-que-no-se-lleva.md) | Lo que funcionó (o se probó y se revirtió) en el origen y NO se copia, y las ideas de fondo. |

## Cómo se actualiza

Lo normal es la regla de arriba: cada lección entra cuando aparece. Para una pasada completa a pedido
(«actualizá el kit»):

1. **Qué cambió:** en cada repo activo del dueño, `git log --since=<fecha del último commit de esta carpeta>`
   sobre su `CLAUDE.md`, `.claude/` y sus docs de método; y el historial del `CLAUDE.md` global.
2. **Filtrar:** entra lo TRANSFERIBLE con su gatillo escrito; a cada capa lo suyo (tabla de arriba). Lo que se
   probó y se revirtió va a `lo-que-no-se-lleva.md` con el motivo: es tan útil como lo que quedó.
3. **Sanear:** un `grep` de los nombres de producto, personas y clientes de cada repo sobre esta carpeta da vacío.
4. **Refutar:** UN subagente adversarial intenta tumbar cada pieza nueva o cambiada con la vara de arriba.
   Lo que no aguanta, sale.

## La regla que ordena el kit

> **Nada se adopta «por completitud». Cada pieza tiene un gatillo escrito.**

El error más caro con esto es copiar el arnés maduro de un proyecto de meses a un repo con cero usuarios: ahí
no protege nada y compite por el contexto con el trabajo real. `dia-1.md` va sí o sí; lo demás espera su gatillo.
