# CLAUDE.md — <NOMBRE DEL PROYECTO>

> **Se carga ENTERO en cada sesión. Techo: 15 KB, con un control que FALLA, y el número no se sube:** cuando
> aprieta, la única salida es partir. Las reglas de cómo trabajo con el dueño viven en su `CLAUDE.md` global y
> rigen solas: **no se copian acá** (una copia se desincroniza y hace cumplir la versión vieja).

## Qué es esto / norte

<Qué es el producto, para quién, qué es lo prioritario. Tres a cinco líneas.>

## Dónde va cada cosa que se quiere dejar escrita

A UNO de cinco destinos. Si el dueño pide «documentá esto», se le dice a cuál:

| Si es… | Va a… |
|---|---|
| **Estado** (qué falta, qué espera, qué está roto) | un **ticket**, nunca prosa. Los docs lo citan por número. |
| **Una medición** | fuera, o congelada: el número con su fecha y el comando para volver a medirlo. |
| **Algo para que Claude no se equivoque** | un **control** (freno o aviso automático), y el texto se borra en el mismo commit. |
| **Historia** (qué pasó, quién, cuándo) | el historial de versiones. **Ni fecha ni quién en docs, comentarios ni docstrings.** |
| **Conocimiento** (cómo funciona, por qué) | `docs/`, o el docstring si se ve leyendo UN archivo. Los docs dicen solo lo que cruza archivos. |

**Qué entra a ESTE archivo:** solo lo que cambia lo que hago en CUALQUIER chat de este repo; lo de un área va a
su doc aunque sea importante. *Si una frase puede volverse falsa sin que nadie la toque, no va acá.* La regla
**de negocio** se queda mientras rija; el **parche** por un error de Claude es provisorio: sobra si hay un
control, y si no, se vuelve a probar con cada modelo nuevo.

**Para quién es la doc:** <A — solo la IA la relee: cada doc abre con la pregunta que contesta, sin anécdota,
lo cerrado se borra / B — la releen personas: se conserva el relato del porqué y lo cerrado no se borra.>

## Cómo trabajamos

- **Quién escribe el código:** <Claude / los dos>. **Quién decide el rumbo:** <el dueño>.
- 🔴 **Un error repetido se vuelve un CONTROL, no un párrafo**: al segundo tropiezo de la misma clase, el
  chequeo se escribe en el mismo trabajo y **enganchado al pipeline en ese commit** → `docs/patrones-de-control.md`.
- **Commit por PIEZA TERMINADA**, no por sesión: es el único deshacer cuando el que edita no recuerda qué editó.
- **Tickets:** un tipo y un área por ticket; el que espera algo lleva su **gatillo** en la primera línea. Se
  cierran con `Closes #N` en el commit; lo que queda para después sale antes a su propio ticket (un cierre
  automático no lee el cuerpo). Lo decidido que no se cierra con el motivo.

## Reglas duras del producto

<Una línea por área que el proyecto tenga, apuntando a su doc (plantillas en `reglas-por-area.md` del kit):
datos y autorización, errores, listas, interfaz, IA, publicación. Acá solo la regla que de verdad cambia
CUALQUIER chat; el resto, en el doc del área.>

## Punteros

| Para… | Leer |
|---|---|
| Qué falta / qué puede romper | los tickets abiertos (`gh issue list`) |
| Los innegociables del día 1 | `docs/dia-1.md` (su estado, en tickets) |
| Cómo se escribe un control que no se pudre | `docs/patrones-de-control.md` |
| Qué se agrega al arnés y con qué gatillo | `docs/escalar-el-arnes.md` |
