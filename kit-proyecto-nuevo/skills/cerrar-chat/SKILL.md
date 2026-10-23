---
name: cerrar-chat
description: Cierre LIVIANO de una conversacion (2-3 turnos, sin subagentes). Usar SIEMPRE que el usuario diga "cerra/cerremos este chat", "cerrar el chat", "cerremos aca", "damos por cerrado", o pida cerrar OTRO chat desde una conversacion nueva.
---

> **Plantilla del kit.** Copiar a `.claude/skills/cerrar-chat/` del proyecto y completar los `<…>`; lo que no
> aplique, se borra. Lo que no se toca: liviano y sin subagentes.

# Cerrar un chat — liviano, sin auditor

Deja las cuentas al día en **dos o tres turnos, sin subagentes**.

🔴 **Sin subagente auditor, y no se re-agrega «por las dudas».** Medido en el proyecto de origen: el cierre con
auditor se llevaba el 15-20 % del gasto semanal, encontraba ~5 cosas por cierre y en 8 semanas nunca bajó.
Documentar es trabajo del momento; la auditoría de la doc se hace una vez por versión, en la revisión de
publicar (si el proyecto la tiene).

**Qué NO es:** «commiteado pero sin publicar» no es un pendiente. Nunca empujar a publicar al cerrar.

## Pasos (de corrido, sin pedir confirmación)

1. **Control automático del proyecto**, si existe: `<comando del chequeo de consistencia>`. Un rojo se
   arregla ahora.
2. **Tickets que tocó el chat:** lo que quedó a medias o espera algo → abierto, con el estado al día (y su
   gatillo en la primera línea si espera algo); lo terminado con código → el renglón `Closes #N` en el commit
   que lo termina (lo que quede para DESPUÉS de publicar sale antes a su propio ticket); lo terminado sin
   código → cerrarlo. Un pendiente nuevo → ticket nuevo, nunca un párrafo en un doc.
3. **Repaso de la documentación, sin subagente:** con lo que ya está en el contexto, confirmar que lo
   significativo del trabajo quedó en su destino (ticket, control, doc o docstring); lo que falta se escribe
   ahora, no se avisa.
4. <Lo propio del proyecto al cerrar, si tiene: borrador de novedades, buzón de pedidos, avisos vivos.>
5. **Commit + push** de lo que quede del chat (skill `commitear`: solo sus archivos) y, si la pieza está
   terminada y validada y el proyecto trabaja con copias aparte, **integrarla** a la rama de desarrollo. Si
   frena por algo que no se destraba solo, queda en su rama y se dice en una línea.
6. **Reportar en 2-3 líneas**, en el idioma del dueño: qué quedó, qué se arregló. Sin empujar deploy.

**Cerrando OTRO chat:** lo mismo, reconstruyendo qué tocó desde el `git log` reciente y sus tickets.
