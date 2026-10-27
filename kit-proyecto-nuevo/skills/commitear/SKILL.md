---
name: commitear
description: Commitear y pushear sin las trampas de git en Windows. Usar SIEMPRE que el usuario pida "commiteá", "comité", "pusheá", "puyá", "subí esto a dev" o equivalente. Solo los archivos de ESE chat, nunca git add -A.
---

> **Plantilla del kit.** Copiar a `.claude/skills/commitear/` del proyecto y completar los `<…>`. Las trampas
> de la consola de Windows viven en el `entorno-windows.md` del repo de configuración global: no se copian acá.

# Commitear y pushear

## Reglas

1. **Commit + push de una pieza terminada y validada = sin preguntar**, a la rama de trabajo
   (`<rama de desarrollo, o la de la copia aparte del chat>`). «Commitear» incluye pushear. A la rama
   publicada, solo publicando.
2. **Solo los archivos de ESE chat, nunca `git add -A`.** Y la ruta explícita no alcanza si el índice ya
   trae algo de otro chat: `git add` agrega al índice y `git commit` se lleva el índice ENTERO. Por eso
   **siempre `git commit -F <msg> -- <rutas>`**, y antes un `git diff --cached --stat`. Si un archivo lo tocó
   también otro chat, mirar su diff y confirmar que todo lo que aparece es propio.
3. **La rama se lee de verdad** (`git rev-parse --abbrev-ref HEAD`), nunca del dato del arranque de la sesión.
4. **Nada de saltear hooks** (`--no-verify`) ni rodear un freno por otro camino. Si un hook frena, se arregla
   lo que marca.
5. **El merge a la rama publicada es siempre squash**, y su mensaje cierra con `Origen en dev: <sha>`: después
   de un squash las dos ramas no comparten historia, y ese renglón es el ancla para saber qué viajó.

## Receta

1. Mensaje a un archivo con la herramienta de escritura, **con nombre ÚNICO por corrida** (la rama más un
   número al azar, en la carpeta temporal): con un nombre fijo, un agente commiteó con el mensaje de otro.
   Título `tipo(área): resumen`, cuerpo con qué y por qué, y la línea `Co-Authored-By` que indique el sistema
   en ese chat.
2. `git diff --cached --stat; git add <rutas>; git commit -F <msg> -- <rutas>; git push origin <rama>`
   (en PowerShell 5.1, encadenado con `; if ($?) { … }`).
3. Si el push lo rechaza por `non-fast-forward`: `git pull --no-rebase` y volver a pushear. **Nunca
   `--rebase` ni `--autostash`** con trabajo de otro chat en el disco.
4. Verificar que el push reportó la rama, y borrar el archivo del mensaje.
5. **Si el pre-commit avisó gatillos cumplidos sin decisión** (`chequear_gatillos.py`): adoptar, abrir el ticket
   o declarar «no» con motivo en `docs/gatillos.json`, en ese mismo trabajo, y decírselo al dueño en una línea
   y en lenguaje de negocio. Un aviso que se deja pasar commit tras commit entrena a no leerlo.
