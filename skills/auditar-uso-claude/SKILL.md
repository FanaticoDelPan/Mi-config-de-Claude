---
name: auditar-uso-claude
description: Audita cómo el usuario usa Claude Code analizando su historial completo de conversaciones (~/.claude/projects). Úsala cuando pida "auditá mi uso de Claude Code", "analizá cómo uso Claude", "en qué puedo mejorar mi forma de pedir", o quiera repetir esta auditoría en otra computadora. Produce un diagnóstico con qué mantener, mejoras activas (cómo pedir) y mejoras pasivas (skills/config a crear).
---

# Auditar uso de Claude Code

Objetivo: revisar el historial real de prompts del usuario y devolver una auditoría
accionable sobre **cómo usa Claude Code y cómo mejorarlo**. No es un resumen de proyectos:
es sobre el *método de trabajo* del usuario.

## Procedimiento

1. **Extraer datos.** Corré el script que vive al lado de este archivo:
   ```
   powershell -ExecutionPolicy Bypass -File "<dir-de-esta-skill>\extraer.ps1"
   ```
   Imprime métricas (total de prompts, largo promedio/mediana, señales por tema, slash
   commands, actividad por hora, por proyecto) y vuelca todos los prompts limpios a
   `%TEMP%\cc_prompts.txt` en UTF-8. (En no-Windows no aplica; el historial vive igual en
   `~/.claude/projects/*/*.jsonl` — adaptá el parseo si hiciera falta.)

2. **Leer el volcado.** Leé `cc_prompts.txt`. Es grande: leé la cabecera, las sesiones con
   más prompts, y usá Grep sobre el archivo para los temas que marcaron alto en las métricas.
   No hace falta leerlo entero.

3. **Clasificar patrones.** Buscá, con evidencia citada:
   - Tipos de pedido que se **repiten** (candidatos a skill).
   - Momentos de **fricción**: correcciones, "no funciona", "¿estás seguro?", regresiones.
   - **Brechas de comprensión**: "no entiendo", "explicame", "¿qué es...?", pedidos de subir
     el nivel de abstracción.
   - **Fricción de entorno**: cómo se corre/verifica la app, pasos manuales repetidos.
   - Lo que el usuario hace **bien** y conviene mantener.

4. **Entregar la auditoría** en español, con esta estructura:
   - **Qué mantener** (hábitos buenos, con ejemplo).
   - **Mejoras activas** (cómo pedir / qué contexto dar) — concretas, con el "antes → después".
   - **Mejoras pasivas** (skills a crear, ajustes a CLAUDE.md, permisos) — cada una con el
     patrón que la justifica y su impacto.
   Rankeá por impacto. Recomendá primero; implementá solo si el usuario aprueba.

## Calibración del usuario (lo que ya sabemos — verificar, no asumir ciego)

- **No programa.** Claude escribe todo el código; él dirige producto y decisiones. Quiere
  explicaciones a **alto nivel de abstracción**, sin jerga, idealmente con números/analogías.
  ~1 de cada 3 prompts pide entender algo. Tratar las explicaciones como entregable, no como ruido.
- **Dicta por voz.** Prompts largos (mediana ~760 chars), conversacionales, con varias cosas
  mezcladas. Hay errores de transcripción frecuentes de términos técnicos — interpretá la
  intención. Glosario observado:
  `cloud`/`cloud code`/`Cloud` → Claude/Claude Code · `cloud md`/`claude md` → CLAUDE.md ·
  `punto bat` → `.bat` · `Superbase`/`SupaBase` → Supabase · `Sonett`/`Sonet` → Sonnet ·
  `COVID`/`comitiar` → commit/commitear · `Jardines` → harness · `CEO` (en contexto Google) → SEO ·
  `dominion` → dominio · `analcisconia`/`menisconía` → análisis con IA.
- **Trabaja de noche** (pico 21h–1am, después del trabajo). Sesiones largas, a veces cansado.
- **Dos computadoras** (casa + oficina) sincronizadas por git. OJO: las skills y el
  `~/.claude/CLAUDE.md` global NO viajan en el repo del proyecto — hay que replicarlos a mano.

## Notas

- Las cifras cambian con el tiempo; re-correr el script da el estado actual.
- Los buckets de temas en `extraer.ps1` son editables: ajustá las regex si cambian los patrones.
