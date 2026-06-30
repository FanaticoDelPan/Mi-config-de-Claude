# Prompt — Armar la arquitectura de documentación en un proyecto nuevo

> **Para qué existe:** prompt reutilizable para pegar al empezar (o a mitad de) cualquier proyecto, y que
> Claude monte y mantenga la documentación con la misma arquitectura que funcionó en SkyOne.
> **Cómo se usa:** copiá el bloque de abajo y pegámelo. Lo único que conviene completar a mano es el
> corchete del punto 8 (audiencia). Si el proyecto YA tiene docs, sumá la línea del final de "Notas".

---

## El prompt (copiar desde acá)

Quiero que armes y mantengas la documentación de este proyecto con una arquitectura concreta. No es un "escribime un README": es un sistema de docs que vas a sostener vos en cada trabajo. Reglas:

**1. Foto vs. detalle.** Creá UN solo archivo central corto (`CLAUDE.md` o equivalente) que se cargue siempre al empezar. Adentro va SOLO: el norte del proyecto, las reglas duras, el estado actual (una foto breve) y un índice de punteros al resto. Todo el detalle (cómo se resolvió cada cosa, evidencia, narración) vive **afuera**, en `docs/`, linkeado. El archivo central se mantiene corto a propósito: es lo que leés en cada sesión, si engorda se vuelve caro y lento.

**2. Una cosa, un solo lugar (fuente única de verdad).** Cada dato vive en exactamente un archivo. El número de versión en uno y solo ahí; los pendientes en otro; el historial en otro. Nada repartido, nada duplicado. Si encontrás el mismo dato en dos lados, es un bug: consolidalo.

**3. Cuatro estados de información que no se mezclan:**
- **vivo** (lo vigente, estado actual) → en el archivo central
- **histórico** (lo ya hecho, cómo se llegó) → `docs/historial.md`
- **por-qué** (decisiones y su justificación) → `docs/decisiones.md`
- **pendiente** (lo que falta y lo que puede romper) → `docs/pendientes.md`

**Regla de oro:** cuando algo deja de ser "lo de ahora", lo movés al histórico **en el mismo trabajo**, no después. Así el central nunca engorda.

**4. Mantener la doc es parte de la tarea, no un después.** Se actualiza en el mismo commit que el cambio que la vuelve cierta. Filtro mental antes de escribir algo en el central: *"¿esto es una regla/estado vigente, o es relato de algo ya hecho?"* Si es relato → va a `docs/`.

**5. Guías de un solo archivo para lo repetitivo.** Cada tarea que se hace seguido (publicar, deployar, agregar un componente, etc.) tiene UNA guía completa con todas sus trampas, no info desperdigada en cinco lados. Si las guías se multiplican o se pisan, frená y proponé consolidar.

**6. Cada documento se autoexplica.** Todo archivo de `docs/` arranca con un encabezado de 1-2 líneas: para qué existe / qué es / a quién apunta. Abro cualquiera y entiendo su rol en 3 segundos.

**7. Las lecciones se escriben donde duelen, con fecha.** Cada regla no obvia lleva atrás el error concreto que la originó ("esto existe porque pasó tal cosa el tal día"). La doc no es teórica, es cicatriz: así no se repite el error ni se borra la regla por parecer arbitraria.

**8. Audiencia explícita / dos registros.** Definí para quién escribís cada cosa. [COMPLETAR según el proyecto: p.ej. "a mí, no técnico, me hablás en lenguaje de negocio; los docs internos pueden ser técnicos".]

**9. La doc va al repo, no a tus memorias.** Todo el contexto del proyecto viaja con `git pull` a cualquier máquina. Única excepción innegociable: los **secretos** (contraseñas, tokens) JAMÁS al repo — en el repo se documenta solo dónde están, nunca su valor.

**10. Lo que se hace seguido sube de prosa a acción disparable** (un skill / comando), cuando ya esté estable. De "explicación que leo" a "rutina que ejecutás".

**Arrancá ahora:** mirá qué proyecto es, proponeme la estructura concreta de archivos (nombres y qué va en cada uno) adaptada a esto, y cuando la apruebe la creás. No la armes a ciegas: primero el árbol, después el contenido.

---

## Notas de uso

- **Punto 8 (audiencia):** es lo único que conviene completar vos antes de pegar. Define el registro
  (negocio vs. técnico) y para quién se escribe cada capa.
- **Proyecto que YA tiene docs:** agregá al final del prompt → *"Ya hay documentación; primero auditá lo
  que existe y proponeme cómo migrarlo a esta estructura, no empieces de cero."*
- **Lo que no se transfiere solo:** el punto 7 (cicatrices con fecha) nace del uso. El prompt instala el
  hábito de anotarlas; las lecciones reales se acumulan con los meses.
- **Origen:** destilado de la arquitectura de docs de SkyOne (`SkyIA-Pro-Max-Ultra`), 2026-06-30.
