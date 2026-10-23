# Lo que NO se lleva, y el patrón de fondo

> **Qué contesta:** qué prácticas del proyecto de origen NO se copian a un repo nuevo —las que funcionaron
> allá por motivos que no viajan, y las que se probaron y se revirtieron— y las ideas de fondo de las que sale
> todo el kit. Si dudás de sumar algo que no está en `dia-1.md` ni en `escalar-el-arnes.md`, mirá primero acá.

## Lo que funcionó allá y NO se lleva

| # | Qué | Por qué no — y lo único que sí se lleva |
|---|---|---|
| 1 | **Presupuesto de peso blando y calibrable** (pre-aviso, excepciones declaradas, recalibrar) | Se subió nueve veces en dos semanas. **Se lleva la versión dura** (`escalar-el-arnes.md` §Presupuesto de peso): falla, tiene candado y la única salida es partir. |
| 2 | **Un mapa aparte de reglas duplicadas** | Es un tercer lugar que se desincroniza: después de un cambio de método quedaron copias viejas que cazó una auditoría, y cambiar una regla obligó a sincronizar nueve archivos. **Se lleva:** el control de prosa repetida y el aviso «esto es una copia, manda tal lado» pegado a la copia. |
| 3 | **Un orquestador de controles propio** | Reimplementa lo que la CI da gratis; el script de consistencia del origen llegó a 143 KB. **Se lleva:** cada control, un script chico; lo barato antes que lo caro. ⚠ Y el corte en la primera etapa roja vale solo para la CI barata: en la corrida cara de publicar fabricó siete pasadas de ~30 min con una sola en verde. Ahí se muestran todos los rojos de una, se arreglan en tanda, se re-corre solo lo que falló y al final va UNA pasada entera. |
| 4 | **Un repartidor propio de navegadores** para las pruebas de pantalla | Es el comportamiento por defecto de la herramienta estándar. |
| 5 | **Numerar los cambios de base a mano** | Fabrica los choques que después hay que controlar. |
| 6 | **Componentes de interfaz hechos a mano** | **Se llevan los tokens**; los componentes, de librería. |
| 7 | **Aislar tus propias pantallas con marcos y mensajería** | En la web no hay objeto privilegiado que proteger. **Se lleva:** la identidad del que manda un mensaje se prueba por la REFERENCIA de la ventana. |
| 8 | **El aparato de «hasta qué versión es seguro volver»** | Existía porque convivían dos versiones contra la misma base. **Se lleva:** si decide una persona bajo presión, la señal va donde esa persona mira. |
| 9 | **Detectar pisadas entre chats en la misma carpeta** | El arreglo es no compartir carpeta. **Se lleva** la versión barata: frenar la PRIMERA edición en la carpeta compartida y mandar a la copia aparte (`escalar-el-arnes.md`). |
| 10 | **Medir el tamaño mínimo de pantalla contra el parque real de máquinas** | Con usuarios de afuera no hay parque. **Se lleva:** UN piso verificado por una máquina. |
| 11 | **Una regla de literalidad del pedido** («publicá» autoriza, «cuando publiquemos» no) | Es prosa custodiando la acción más irreversible. **Se lleva:** que lo irreversible lo dispare algo que se teclea. |
| 12 | **Publicar de noche, ramas retenidas, novedades en video, avisos de integraciones caídas** | Dependen del producto, del server o del horario del dueño. |

## Lo que se probó allá y se revirtió

Tan útil como lo que quedó: son las buenas ideas que no rindieron, con el motivo medido.

| Qué | Por qué se sacó |
|---|---|
| **OK del dueño para integrar una copia a la rama de desarrollo** | Duró un mes: era un trámite. El dueño contestaba «dale» sin aportar nada. |
| **Tests de lo tocado y pantallas exigidos al integrar** | En cuatro semanas, ~27 frenos con 0-1 defecto real; las pantallas se llevaron ~5,6 h de PC en 9 días. Pasaron a correr al publicar. |
| **Cierre de chat largo y con subagente auditor** | El cierre entero se llevaba el 15-20 % del gasto semanal (el auditor ~5 %; el resto, los turnos del chat con el contexto en su punto más grande), encontraba ~5 cosas por cierre y en 8 semanas nunca bajó: auditar más no volvió la doc más correcta. Pasó a 2-3 turnos sin subagentes. La auditoría de la doc pasó a hacerse una vez por versión, en la revisión de publicar. |
| **Estado del proyecto en prosa** (pendientes y avances en siete docs) | Fabricaba las contradicciones que después auditaba cada cierre; la doc crecía ~72 KB por día. Pasó a tickets, y la doc bajó de 5,8 a 1,6 MB. |
| **Dos modelos en el mismo ángulo de la revisión** | Duplicaba el costo; el registro de hallazgos mostró que uno rendía claramente mejor. Queda como segunda mirada ocasional, decidida en el momento. |
| **Etiqueta manual de «hecho»** en los tickets | La usaron 2 de 280. El cierre por el renglón del commit alcanza. |

## El patrón de fondo

1. **Lo que no verifica una máquina, no existe.** En el origen, la regla con control tenía una excepción en dos
   meses; la misma clase de regla sin control, doscientas violaciones.
2. **Un control también se pudre, y se pudre en verde** → `patrones-de-control.md`. **Y uno sano puede no
   rendir:** se mide en defectos reales contra horas de máquina y falsos rojos.
3. **Un número que se puede mover cuando molesta no es un límite.** O rompe de verdad, o solo se muestra.
4. **El archivo que se lee siempre no dice cómo están las cosas hoy.** El estado vive en tickets.
5. **Quien juzga no es quien produce, y tiene menos herramientas.**
6. **Un arreglo mete una regresión más veces de las que uno cree**, y la vuelta que audita los arreglos no es
   opcional — pero tiene que poder cerrar (`agente-revisor-final.md`).
7. **El arnés compite por el mismo espacio que el trabajo.** Si un tropiezo se puede convertir en control, el
   control REEMPLAZA al párrafo.
8. **Un freno que se esquiva por otro camino no frenó.** Una barrera puesta a propósito se respeta o se
   avisa; nunca se rodea.
