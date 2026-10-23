# Reglas duras por área

> **Qué contesta:** las reglas duras de cada área de un producto (datos, errores, listas, interfaz, IA,
> publicación). **No van al `CLAUDE.md`:** cada área se copia a `docs/reglas-<área>.md` **cuando el proyecto
> tiene esa área**, con un puntero de una línea en el `CLAUDE.md`, y cuando aparece el hook de «reglas que
> llegan solas» (`escalar-el-arnes.md`), le llega a Claude al editar un archivo de esa área.

## Autorización y datos
- 🔴 **La autorización se decide 100% en el servidor y se re-verifica en CADA operación.** Un dato que llega
  del cliente diciendo «este puede editar» sirve solo para pintar un botón. Todos los puntos de entrada
  heredan de la misma base con la guarda, y **un test recorre el árbol y falla si uno se olvidó**
  (`patrones-de-control.md` §Test de cobertura estructural).
- 🔴 **`<tenant_id / owner_id>` NOT NULL en toda tabla de negocio, desde la primera migración** (si es
  multi-cliente), inyectado por una capa —no escrito a mano en cada consulta— con un test que falle si aparece
  una consulta sin el filtro.
- 🔴 **Ninguna versión borra algo que la versión anterior todavía lee.** Lo destructivo va en dos entregas
  (agrega y deja de usar → recién después borra), y un control falla si una migración trae un borrado o
  renombre sin excepción declarada.
- **Las migraciones corren DENTRO del despliegue**, antes de mover el tráfico. Nunca como paso humano aparte.
- **Todo script que escriba datos reales: el flag es `--aplicar`, nunca `--simular`.** El modo seco es el
  default, e imprime el conteo por tipo de cambio antes de tocar nada.
- **Una consulta para contestarle al dueño reproduce los filtros de la pantalla** (primero la baja blanda).
  Si no, da otra realidad, casi siempre la alarmante.
- **Toda exportación masiva escribe una fila de auditoría ANTES de generar el archivo:** quién, qué, cuántas
  filas, cuándo.
- **Borrar de verdad y exportar todo lo de una cuenta son dos caminos implementados y testeados** antes del
  primer usuario de afuera.

## Errores
- 🔴 **Taxonomía CERRADA de causas, decidida en el servidor, pintada por UN solo componente.** Nunca un
  «no se pudo» genérico. La causa se detecta por **código estructurado** (tipo de excepción, código del
  driver, estado HTTP), **jamás parseando el texto del error**.
- ⚠ **Dos relojes distintos son dos causas distintas.** Un timeout de la dependencia y uno de la fila de
  espera para llegar a ella no traen el mismo código.
- 🔴 **Un dato ACCESORIO va en su propia red de manejo de error**, y **el hueco se DICE**: el valor por
  defecto de un dato ausente casi siempre significa algo.

## Respuestas y listas
- **El `total` viaja ANTES de la lista**, y **una respuesta recortada lo DICE**. Vale para pantallas y sobre
  todo para respuestas que consume un modelo.
- **Paginación por cursor obligatoria en toda respuesta de lista**, con tope impuesto por el framework.
- **Toda consulta que cambia de forma se cronometra contra datos reales** y el número se anota (perder un
  tope de filas, sumar un join, mover un filtro al código).

## Interfaz
- 🔴 **Fecha, hora y números salen de UN solo módulo, con idioma y formato fijados EN CÓDIGO.** El módulo y la
  regla de lint que lo hace obligatorio van en el mismo commit.
- 🔴 **Tokens por FUNCIÓN (`--color-peligro`), nunca por apariencia, y se tokeniza color, escala tipográfica
  y espaciado**, cada uno con su regla de lint. Lo que se puede escribir a mano se va a escribir a mano.
- **Las opciones de color son una lista CERRADA** (es lo que permite verificar el contraste de todas).
- **Los componentes, de librería** (diálogos, menús, selects).
- **Qué se recuerda entre visitas:** dónde estabas mirando → se repone · lo que estabas escribiendo → **se
  avisa antes de perderlo** · una selección con alcance de seguridad → vuelve a su valor seguro. **No se
  repone lo que no se ve y cambia lo que hace un botón.**
- **Una pantalla se renderiza y se MIRA**, y antes de darla por terminada, `checklist-pantalla.md`.

## IA (si el proyecto la usa)
- 🔴 **Todo texto que escribió otra persona se envuelve antes de dárselo a un modelo**, con la marca de «esto
  es un dato, no una orden» y el recordatorio **después** del dato. Un solo lugar del sistema lo hace.
- **Guardar el modelo de cada llamada y valuar el consumo errando hacia arriba**; un modelo desconocido se
  cobra a precio de castigo para que un cambio olvidado grite.
- **La cuota corta de verdad, por CUENTA, con un tope duro en la consola del proveedor como red final.**

## Publicación
- 🔴 **El disparador de una acción irreversible no puede ser una interpretación de lenguaje natural.** Que lo
  dispare algo que la persona teclea: un botón, un comando, una etiqueta.
- **Lista CERRADA de qué frena una publicación, con el DESENLACE de cada ítem.** *Todo lo que no está en la
  lista, no frena.*
- **Cada trabajo que se cierra deja su renglón de novedades en lenguaje de usuario, en el momento.**
