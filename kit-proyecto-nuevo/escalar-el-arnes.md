# Qué se agrega al arnés, y con qué gatillo

> **Qué contesta:** qué piezas de control y de proceso se suman a un repo DESPUÉS del día 1, y cuándo. Existe
> para que no se copie todo de entrada: el arnés maduro en un repo con cero usuarios no protege nada, compite
> por el contexto con el trabajo real y se abandona. **Hasta que el gatillo no se cumple, la pieza no se escribe.**
>
> 🔔 **Los gatillos que se pueden contar mirando el repo los vigila `chequear_gatillos.py`** (va a `scripts/`
> con su test; corre en el pre-commit como aviso y en la CI con `--estricto`). Cuando uno se cumple, lo nombra
> hasta que haya una decisión en `docs/gatillos.json`: adoptada, un ticket, o «no» con su motivo. La llave es
> el nombre en negrita de la fila: **renombrar una fila es cambiar el chequeo en el mismo commit**, y su test
> lo verifica. Los demás gatillos siguen dependiendo de que alguien los vea.

## Proceso de trabajo con varios chats

| Pieza | Gatillo — se agrega cuando… | Qué es, en su versión mínima |
|---|---|---|
| **Copia de trabajo por chat** (worktree) | …dos chats escriben el mismo repo | **Todo chat que va a escribir** trabaja en su copia, y el mismo chat la integra a la rama de desarrollo al terminar, sin pedir OK (el OK se probó y era un trámite). Piezas: un hook que hace nacer la copia de la rama de desarrollo (la configuración del harness solo ofrece «la rama abierta» o «la del remoto»); un freno en el arranque si nació de la publicada; un hook que frena la **primera edición** en la carpeta compartida y manda a la copia; integrar con un push que solo avanza, más reintento. 🔴 **Las copias van afuera del árbol del repo si el hook de creación lo permite**; si quedan adentro, ignoradas para git y para las búsquedas (`.gitignore` + `.rgignore`), sabiendo que un `grep -r` igual las ve — en el origen la consistencia y unos tests leyeron copias de otros chats y se pusieron en rojo, dos veces, aun con ignorados configurados. Todo control que recorra el árbol las excluye explícitamente. |
| **Turno de integración** (una copia a la vez) | …se ve el rebote en bucle al integrar (en el origen, con 2-4 chats integrando a la vez) | Un candado del sistema operativo (mutex con nombre) que toma quien integra: si el proceso muere, se suelta solo — un archivo de candado quedaría tomado. Si la rama avanzó sin choques, mezcla solo. |
| **Lo pesado fuera del chat** | …la suite entera pasa de ~3 min, o hay 3+ chats en paralelo en una sola PC | El chat valida **su pieza** (los tests de lo tocado). La suite entera y las pantallas completas corren **al publicar** y en una corrida diaria sobre la rama de desarrollo; el rojo de la diaria lo avisa el arranque del chat siguiente. Medido en el origen: la validación «liviana» escalaba a suite entera en 6 de cada 10 integraciones. |
| **CI al publicar + diaria, en vez de en cada push** | …la CI cuesta plata de verdad (en el origen: ~750 corridas en un mes, ~5.400 min de máquinas Windows) | Se mueve el disparador, no se borra el control. Al integrar quedan solo los de segundos (lint, consistencia, secretos). |
| **Reglas que llegan solas** | …existe la primera guía de un área (pantallas, base, etc.) | Un hook que, antes de editar un archivo de esa área, le pone a Claude la guía UNA vez por chat. Medido en el origen: la guía de pantallas la abría menos de 1 de cada 5 chats que tocaban una vista. Corolario: los archivos se editan con las herramientas de edición, no por consola — el hook no ve una edición de consola. |
| **Probar las instrucciones** | …llega un modelo nuevo, o pasaron ~90 días | Una batería de pedidos que re-prueba los **parches** de comportamiento del `CLAUDE.md`. Se corre en un **clon** con la subida apagada y **sin credenciales de git ni de GitHub**: en el origen, un chat de prueba encontró la subida apagada, subió desde el repo de al lado y abrió un ticket real con una decisión inventada. Lo que pasa sin el parche, el parche sale. |

## Controles

| Pieza | Gatillo | Qué es |
|---|---|---|
| **Guarda de rama** | …existe algo publicado que se puede romper | Hook `pre-commit` que compara la rama declarada contra la real y **bloquea** (fail-closed). ⚠ Viaja por `core.hooksPath`: en un clon nuevo está apagado hasta que lo instala el mismo comando que levanta el proyecto. |
| **Test de fronteras arquitectónicas** | …**rompés una frontera por primera vez** | Análisis de imports que falla si se cruza. Apuntado a la frontera que de verdad se cruza (el núcleo del que todos tiran), no a la que dibuja el árbol de carpetas. |
| **Sin fechas ni autores en el código y los docs** | …aparece la primera fecha en un comentario o docstring | Trinquete **por archivo** contra la rama publicada (por total dejaba ~450 de margen para volver a crecer). La fecha de una medición se permite. |
| **Prosa repetida** | …hay ~10 docs | Busca tramos de 15+ palabras repetidos entre docs, con trinquete contra la rama publicada. En el origen casi un tercio de lo que crecía la doc narraba lo que ya decía el docstring. |
| **Validador de enlaces internos** | …hay dos documentos | **Valida el ANCLA, no el archivo** (en el origen, «todos los punteros resuelven» con dos que apuntaban a encabezados inexistentes). El mismo bucle al revés da el control de huérfanos. |
| **Chequeo de pantallas completo** | …se escapó a producción un bug de esa clase | El día 1 son 30 líneas: abrir cada ruta y fallar por excepción, promesa rechazada, `console.error`, cuerpo vacío y desplazamiento horizontal. ⚠ El banco de datos de prueba por pantalla es lo que cuesta y lo primero que se pudre. |
| **Comparador de esquema contra la base viva** | …aplicás migraciones **a mano** fuera del pipeline | Si corren dentro del despliegue, alcanza con correr la cadena desde cero contra el motor real en CI. |

## Presupuesto de peso

| Pieza | Gatillo | Qué es |
|---|---|---|
| **Tope del `CLAUDE.md`** | **día 1** (`dia-1.md` #14) | Un control que **falla** al pasar el tope, más un candado que compara el número contra la rama publicada y frena si subió. **La única salida es partir.** Medido en el origen: desde que el número dejó de poder subirse, partir alcanzó siempre y nunca hubo que perder una regla. Lo que más lo achicó, igual, fue el **criterio de qué entra** (la semilla lo trae), no el tope. (El régimen con excepciones y recalibración, que se subió nueve veces en dos semanas, sigue en `lo-que-no-se-lleva.md`.) |
| **Tope del cuerpo de cada skill** (~20 KB) y **descripciones solo con disparadores** | …el primer skill propio | «El camino en el skill, el porqué en su doc». En el origen el skill de publicar bajó de 67 a 31 KB y el de interfaz de 40 a 8, con todo en verde; las descripciones quedaron solo con los disparadores. |
| **Alarma del total de la doc** | …~30 docs | En **proporción contra el producto**, no un total fijo (el fijo saltaba cada 2-3 semanas sin que sobrara nada). Partir deja el total neto igual o menor. |

## Producto

| Pieza | Gatillo | Qué es |
|---|---|---|
| **Revisor adversarial antes de publicar** | …la primera publicación con usuarios | `agente-revisor-final.md`. En un proyecto chico arranca con UN revisor que cubre los cuatro ángulos; pasa a uno por ángulo + refutador cuando el registro de hallazgos lo justifique. |
| **Registro de hallazgos por ángulo y de escapes a producción** | …~5 publicaciones revisadas, o hay que decidir podar ángulos o cambiar de modelo | Es lo que vuelve falsable el esquema de revisión. En el origen decidió con números qué modelo revisa: uno trajo 15 reales y 2 falsas alarmas contra 11 y 7 del otro. |
| **Revisar las tarjetas de un QA de uso antes de que lleguen al dueño** | …la primera pasada de QA con el dueño decidiendo | UN refutador. En el origen tocó 17 de 21 tarjetas: seis cuestionaban una decisión escrita sin decirlo y cinco tenían una foto que no mostraba lo que decía el texto. |
| **Interfaz declarada + descubrimiento automático** | …hay un **tercero** escribiendo piezas | Un `Protocol` mínimo y un `discover()` con cada carga en su `try`. Antes alcanza la carga defensiva por ítem y una **clave estable** por pieza. ⚠ Para la superficie sensible, lista explícita, nunca descubrimiento. |
| **Autorización por (usuario, componente)** | …va a haber embeds, plugins o integraciones de terceros | 🔴 **La decisión se toma el día 1 aunque la respuesta sea «nunca» — y se escribe.** Agregar el segundo eje después obliga a auditar cada llamada existente. |
| **Aislar en marcos separados** | …embebés contenido que **no escribiste vos** | Nunca para tus propias pantallas. La identidad de quien manda un mensaje entre ventanas se prueba por la **referencia** de la ventana, jamás por el texto del origen (un marco aislado tiene origen `null`). |
| **Método para conectar sistemas de otros** | …el proyecto se conecta por primera vez a un sistema que no es suyo (un ERP, un programa instalado, una casilla, la base de un cliente) | `conectar-herramientas.md` a `docs/`: investigar en la documentación del fabricante con fecha, la vía menos peligrosa, solo lectura de entrada, nunca escribir en la base de un programa instalado, y una prueba que demuestra que escribir falla por permiso. |
| **Novedades acumuladas por persona** | …el producto se **instala** y alguien puede saltearse versiones | Desde el día 1 y gratis: la carpeta de renglones pendientes de publicar. |
| **Piso de rollback** | …la **primera** migración destructiva de verdad | Escribir cuál es la versión más vieja a la que se puede volver, y que el botón de rollback lea ese dato. |
| **Ley de dónde vive cada hecho, extendida** | …hay más de ~10 documentos, **y solo con un control** | La semilla ya trae los cinco destinos. La tabla de dueños por tema sin control ya se demostró insuficiente. |

## La regla de los instructivos

🔴 **Un tropiezo entra a un instructivo SOLO si no se puede convertir en control. Si se puede, el control
REEMPLAZA al párrafo en el mismo commit.** Sin esa regla, un runbook crece un párrafo por cada cosa que salió
mal, y en el origen el instructivo de publicar llegó a pesar más que todo el reglamento y a dejar sin contexto
a la revisión adversarial que corría adentro.
