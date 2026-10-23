# Repaso antes de dar una pantalla por terminada

> **Por qué existe esta lista.** Es una familia de errores que **no falla, no tira excepción y no lo agarra
> ningún test**: la pantalla simplemente queda mal. Y es una familia que el entorno de quien programa
> resuelve solo —tu máquina tiene el idioma correcto, el tema correcto y una pantalla grande— así que quien
> escribe el código es la última persona del mundo que va a verlos.
>
> **Lo único que los caza es una lista.** Los ítems marcados 🤖 se pueden convertir en control automático y
> **hay que hacerlo**; el resto se mira.

---

## Formatos — la regla de fondo

> **El formato es una propiedad del DATO, no del navegador de quien mira.** Si depende de la configuración
> de cada uno, el mismo registro dice 07/03 para uno y 03/07 para otro.

- 🤖 **Todo formato sale del módulo central**, con idioma y formato fijados en código. Ninguna pantalla llama
  a la función de formateo del navegador por su cuenta → regla de lint sobre `toLocaleString`,
  `toLocaleDateString`, `Intl.` fuera de ese módulo. **Va en el mismo commit que el módulo.**
- Fecha en **día/mes/año**, nunca mes/día/año.
- Hora en **24 h**.
- Coma decimal y punto de miles (o lo que corresponda al idioma del producto), y **consistente**.
- **Moneda explícita**: «$» solo no alcanza cuando hay más de una moneda posible en el mundo del producto.
- **Qué columna guarda hora universal y cuál hora local**: mirarlo, no adivinarlo. Es la fuente número uno
  de bugs de «un día de diferencia» — tomar los primeros 10 caracteres de una fecha universal resta un día.
- Textos en el idioma del producto. **Los mensajes del navegador y los `placeholder` son los que más se
  escapan.**

## Controles que dibuja el navegador y no tu página

No son HTML tuyo, así que nadie los prueba y ningún test los ve.

- **`color-scheme` declarado junto a cada bloque de tokens de tema.** Es lo único que hace que el navegador
  pinte sus propios controles con el tema de la app.
- **Mirar en tema claro Y en tema oscuro**: el calendario que se abre en un campo de fecha, la flecha de un
  desplegable, las barras de desplazamiento, el autocompletado.
- **Idioma específico en la etiqueta raíz** (`es-AR`, no `es`).
- 🔑 **Lo que el navegador no deja controlar —el orden de los casilleros de un campo de fecha— no se combate
  reemplazando el control.** Se pone **debajo** una lectura de vuelta en palabras y con el día de la semana:
  *«viernes, 14 de agosto de 2026»*. Delata al instante un 07/03 cargado queriendo decir 03/07, y conserva
  toda la accesibilidad y el teclado que el control nativo da gratis.

## Tamaño y escala

- 🤖 **Nada de valores de tamaño escritos a mano**: escala tipográfica y espaciado tokenizados igual que el
  color, con su regla de lint. *Lo que se puede escribir a mano se va a escribir a mano* — en el proyecto
  auditado el color tiene 1 excepción declarada y el tamaño de texto, **207 incumplimientos**, porque uno
  estaba tokenizado y el otro no.
- 🤖 **Sin desplazamiento horizontal del cuerpo de la página** en el ancho mínimo soportado. **Un solo piso,
  verificado por una máquina**, en vez de una escalera de puntos de corte que nadie comprueba.
- **Cede el aire, nunca el texto.** El ancho fijo es el bug, no el monitor.
- Una tabla ancha **se desliza entera** con el encabezado quieto: **jamás se esconden columnas**.
- 🤖 **La primera fila de datos tiene que verse** sin desplazar. Los avisos y encabezados tienen presupuesto
  de alto; lo que sobra va al pie o a un clic. ⚠ Si automatizás esto, **el punto de medición lo tiene que
  poner el sistema de diseño, no la pantalla medida.**
- **Mirar cómo queda en un celular**, aunque el producto sea de escritorio.

## Estados que existen y nadie dibuja

- **Vacío** («todavía no hay nada» ≠ «no encontré nada con ese filtro» — son dos pantallas distintas).
- **Cargando**, y que no salte el contenido cuando llega.
- 🤖 **Error, clasificado por causa** (dependencia caída / sin permiso / dato inválido / inesperado con
  identificador de correlación), con **su acción** al lado. Nunca un «no se pudo» genérico.
- 🔑 **Un dato accesorio que falla no puede llevarse puesta la pantalla.** Va en su propia red de manejo de
  error — **y el hueco se dice**: el valor por defecto de un dato ausente casi siempre significa algo, y suele
  ser lo más alarmante.
- **Si la pantalla de error TAPA la vista, tiene que traer su propia salida.** «Reintentar» no es salir, y la
  tecla Escape no está escrita en ningún lado.

## Acciones

- Toda acción da **respuesta visible** (no solo que el dato cambie en algún lado).
- Lo destructivo: **deshacer**, o confirmación que diga **qué y cuánto** («borrar 47 filas», no «¿confirma?»).
- **Nunca se recuerda una selección con alcance de seguridad o de borrado**: vuelve siempre a su valor
  seguro.
- **Nunca se guarda en silencio lo que la persona estaba escribiendo**: se avisa antes de perderlo.
- ⚠ **No se repone lo que no se ve en pantalla y cambia lo que hace un botón.** Caso real: un tope de
  resultados repuesto en 20 hacía que «listo: 20 resultados» fuera indistinguible de «no había más».

## Teclado y accesibilidad

- **Foco visible** en todo lo enfocable, y el orden de tabulación sigue el orden visual.
- **Diálogos: atrapan el foco, desactivan el fondo, devuelven el foco al cerrar, cierran con Escape.** Son
  cinco cosas y equivocarse en una lo rompe entero → **usar componentes de librería**, no hacerlos a mano.
- 🤖 **Contraste**: si las opciones de color son una lista cerrada, un script recorre **todas** las
  combinaciones y calcula el ratio real. (Un chequeo eje por eje no encuentra las combinaciones cruzadas: en
  el proyecto auditado una daba 4,49 contra un mínimo de 4,5.)
- **`aria-live` para lo que aparece solo**: avisos, errores, resultados de una búsqueda.
- No usar solo el color para transmitir un estado.

## Y la que nada automatiza

🔴 **Renderizar la pantalla y MIRARLA.** Los controles automáticos verifican que no esté rota; ninguno sabe
si se ve **bien**.

Para que mirarla sea gratis y no un paso aparte que se saltea bajo presión: **que el propio control adjunte
la captura al resultado.**
