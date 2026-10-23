# Cómo se escribe un control que no se pudre

> **La premisa.** Una regla escrita se incumple; lo único que la hace cumplir es una máquina. Pero un
> control es también un activo que se pudre — y se pudre **en verde**, que es la peor forma: deja de
> encontrar cosas y nadie se entera. Estas son las cuatro condiciones, y valen todas juntas o ninguna.

---

## Las cuatro condiciones

### 1. Corre solo
Enganchado al pipeline, al hook, al arranque de la suite. **Nunca a la memoria de nadie.**

**Regla mecánica:** *el commit que escribe un control es el que lo agrega al pipeline. Si no entra al
pipeline, no se escribe.*

Y de ahí sale una regla de citación: **un control que no está cableado no cuenta como chequeo y no se puede
citar como garantía en la documentación.**

### 2. Tiene su propio test de mutación
Un test compañero que **fabrica una violación sintética** y verifica que el control **todavía la cace**.

```python
def test_el_control_de_migraciones_TODAVIA_CAZA(tmp_path):
    """Si este test se pone verde por el motivo equivocado, el control de arriba
    puede haber dejado de encontrar nada y nadie se enteraría."""
    falsa = tmp_path / "0999_falsa.py"
    falsa.write_text("def upgrade():\n    op.drop_table('cualquiera')\n")
    problemas = buscar_operaciones_destructivas([falsa])
    assert problemas, "el control dejó de cazar un drop_table"
```

**Por qué.** El modo de falla real no es el falso rojo: es que cambió un nombre de clase, se movió una
carpeta o cambió el formato del archivo, el control pasa a revisar un conjunto vacío, y queda en verde para
siempre.

### 3. Mide el estado real, nunca una constante copiada
Lo esperado se **deriva** del código o del sistema en el momento: leyendo el árbol sintáctico del script
real, ejecutando la pantalla y observando, consultando el registro. No se escribe a mano en el test.

```python
# MAL: el día que cambie el piso, esta prueba sigue en verde midiendo un valor que ya no existe
PISO_ESPERADO = 90

# BIEN: se lee del archivo que de verdad decide
PISO_ESPERADO = extraer_por_ast(RUTA_DEL_SCRIPT, "PISOS_POR_BORRADO")
```

**El caso que lo enseñó:** un control que verificaba el largo de unos textos los medía **después** de que el
sistema ya los había recortado. Por construcción no podía fallar nunca, y estuvo en verde todo el tiempo que
existió.

**Y el par:** si dos procesos tienen que conocer el mismo dato, se declara **una** vez en un archivo de datos
(JSON/TOML) y lo leen los dos. Nunca dos copias en dos lenguajes sincronizadas por disciplina. Si igual hay
que duplicarlo, el test compara **las dos copias**, no una copia contra un texto.

### 4. El criterio sale de AFUERA del objeto medido
Un control cuyo punto de medición lo declara la cosa medida es una **métrica**, no una barrera — y peor:
transmite sensación de cobertura sin darla.

> *"Quien mueve la marca mueve el arco"* — comentario que el proyecto auditado tenía escrito sobre un
> atributo que la propia pantalla se pone para indicar dónde hay que medir. Se corrigió
> al descubrir que dos pantallas gastaban ~55 % del alto con el control en verde.

**Ancla el control en algo estructural**: un selector genérico del sistema de diseño, la respuesta de red
observada, el registro de rutas. Nunca en un atributo que el objeto medido se asigna solo.

🔑 **Y si el objeto medido igual tiene que aportar el punto** —porque su lista no la encuentra ningún
selector genérico—, que su declaración sea un **PISO y nunca un techo**: se toma el MÁXIMO entre lo que
declara y lo que el control encuentra solo. Así la marca puede empeorar su propia nota, nunca mejorarla. Es
la salida que usó el proyecto auditado, y es más barata que inventar un selector por pantalla (que se cae
al primer cambio de marcado).

**Y el reporte dice siempre el denominador:** «5 de 17 medidas», nunca «OK». Un control que reporta más
cobertura de la que tiene es peor que no tenerlo, porque apaga la revisión manual.

---

## Excepciones: las tres patas

Todo control termina necesitando perdonar un caso. El perdón **nunca** apaga el control ni perdona el archivo
entero.

1. **La excepción se declara en el código del control, con la llave más fina posible y su motivo escrito.**
   ```python
   _DROPS_REVISADOS = {
       # (archivo, operación, tabla) — la operación va en la llave a propósito: sin ella,
       # perdonar el drop_table de una migración regala de yapa todo lo demás que esa migración haga.
       ("0091_retira_tabla_vieja.py", "drop_table", "tabla_vieja"):
           "reemplazada por la nueva en la 0090; nadie la lee desde entonces",
   }
   ```
2. **Un tope de cantidad verificado por el propio control**: `assert len(_DROPS_REVISADOS) <= 3`. *"La lista
   es corta a propósito"* es una intención hasta que hay un número que la hace cumplir.
3. **Tocar la lista de perdones requiere una aprobación distinta de la que aprueba el código** (CODEOWNERS,
   revisor separado, etiqueta). **Si el que rompe la regla es el mismo que se autoriza a romperla en el mismo
   commit, el control es decorativo.**

**Y la excepción que dejó de hacer falta tiene que FALLAR el control, no dejar una nota.** Si al desaparecer
el motivo el control solo imprime un aviso, la lista se pudre a la vista de todos.

⚠ **No dejes listas de excepciones vacías "por si acaso"** con un párrafo explicando cuándo se usan. Se leen
como mecanismos vivos y no lo son. La lista nace con su primera excepción; el motivo queda en el commit.

---

## Test de cobertura estructural

El patrón que convierte una convención en una garantía. Recorre el código por análisis sintáctico y falla si
alguien se olvidó de aplicar la regla.

```python
def test_todo_punto_de_entrada_reverifica_el_permiso():
    revisados = 0
    faltantes = []
    for clase in clases_que_terminan_en("Handler", raiz="src/"):
        for metodo in metodos_publicos(clase):
            revisados += 1
            if not llama_a_alguno(metodo, prefijos=("_denegar", "_ejecutar_con_guarda")):
                faltantes.append(f"{clase.name}.{metodo.name}")
    assert revisados > 30, "el control no encontró nada: cambió la convención de nombres"
    assert not faltantes, f"sin guarda de permiso: {faltantes}"
```

**Las dos líneas que lo hacen funcionar:**
- `assert revisados > N` — sin esto, el día que cambie la convención de nombres el control revisa cero
  métodos y pasa siempre.
- La lista de excepciones **vacía**. Si nace con excepciones, nace muerto.

**Límite honesto que conviene escribir al lado:** verifica **presencia** de la llamada, no que su resultado
se respete ni que corra antes del trabajo. Un `_denegar()` en una rama muerta pasaría. Aun así, la relación
costo/valor es de las mejores que hay: la base son ~40 líneas y el test ~70.

**Apuntalo a la frontera que de verdad se cruza, no a la que dibuja el árbol de carpetas.** En el proyecto
auditado el test de aislamiento cuida que dos módulos no se importen entre sí… y los módulos casi no tienen
código. La frontera que sí está bajo presión —el núcleo de 37.000 líneas donde cualquier archivo importa a
cualquiera— no tiene ningún control, y ya se cruzó.

---

## Duro vs. aviso

Dentro de un mismo control, separar lo que **bloquea** de lo que **se muestra**:

- **Bloquea:** poco, y objetivamente falso — un enlace roto, un test rojo, una regla de seguridad sin guarda.
- **No bloquea:** todo umbral de estilo o de tamaño. Nace no bloqueante o no nace.

**Motivo:** *un rojo permanente por deuda cosmética entrena a ignorar el rojo, y el que importa queda tapado.*

---

## Fail-open vs. fail-closed: se elige una vez, y el camino de emergencia la respeta

- **Fail-open** (deja pasar si el control mismo falla): controles de comodidad diaria. *Una guardia rota no
  puede ser el motivo de que nadie pueda trabajar.*
- **Fail-closed** (bloquea): lo que evita un accidente **raro y caro**.

🔴 **La trampa, y es un caso real:** una guardia diseñada para impedir que una copia de trabajo naciera de la
rama equivocada tenía un camino de emergencia que… la creaba desde donde estuviera parado el repositorio —
que es exactamente el accidente original. **Un camino de emergencia que produce el resultado que el control
prohíbe no es un fail-safe: es el control apagado con pasos extra.**

**Y todo control fail-open necesita su propio test**, verificando el caso **positivo** (que bloquea cuando
debe). Un control que falla abierto y está roto se comporta idéntico a uno que deja pasar legítimamente: no
hay forma de notar que dejó de proteger. **Un guard sin test es un placebo con log.**

---

## Antes de enchufar un control: estimá su tasa de falsos positivos

Contra el estado **normal** del repositorio, no contra el escenario que motivó escribirlo.

**Si el remedio previsto es *"hacelo de nuevo"*, el control no protege: entrena a saltearlo.**

Referencia del proyecto auditado: una guardia con 1.056 invocaciones y 7 frenadas (0,66%) es sana. Otra que
dispara sobre el estado habitual del árbol, no.

---

## Después de enchufarlo: ¿rinde?

Un control sano puede no valer lo que cuesta. **Un freno en el camino de todos los días se mide en defectos
reales cazados contra horas de máquina y falsos rojos, y sale de ese camino si no rinde** (se mueve a donde
sí rinde, por ejemplo al publicar; no se borra). Caso del origen: en cuatro semanas, ~27 frenos al integrar
con 0-1 defecto real, y las pantallas de lo tocado se llevaron ~5,6 h de PC en 9 días.

🔑 **Al reemplazar o mover una garantía, la pregunta es qué caso cubría la vieja**, no qué caso molesta hoy.

---

## Más reglas que salieron de controles que fallaron

- **Una corrida que empieza sobre un árbol y termina sobre otro no vale.** Si alguien editó archivos mientras
  corría, el verde no dice nada de ninguno de los dos: el control anota un sello del árbol al empezar y lo
  compara al terminar.
- **Dónde llega una regla, de más fuerte a más débil:** un freno · un aviso automático en el momento · el
  mensaje del propio control cuando falla · una guía que se carga sola al tocar el área · el docstring. La
  prosa que nadie abre está debajo de todo.
- **El texto que un freno reemplaza se borra en el mismo commit** (en el origen, el commit que sumó unos
  pocos frenos borró ~130 renglones de instrucciones).
