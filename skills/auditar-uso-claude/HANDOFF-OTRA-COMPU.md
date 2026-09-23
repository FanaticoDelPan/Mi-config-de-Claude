# Auditoría de uso de Claude Code — Handoff a la computadora de laburo

> **Cómo usar este archivo (humano, leer una vez):**
> 1. Copiá la carpeta `auditar-uso-claude` completa a `%USERPROFILE%\.claude\skills\` de esta máquina.
> 2. Agregá a tu `%USERPROFILE%\.claude\CLAUDE.md` global el bloque del **ANEXO 1** (nota de dictado).
> 3. Abrí Claude Code en esta máquina y como **primer prompt** escribí:
>    *"Leé `%USERPROFILE%\.claude\skills\auditar-uso-claude\HANDOFF-OTRA-COMPU.md` y seguí lo que dice."*
>    (o pegá el contenido entero de este archivo).
>
> Este archivo es autosuficiente: trae el contexto de la auditoría previa, la consigna, dónde guardar el
> resultado y, en el ANEXO 2, el script por si la skill no se copió.

---

## PARTE A — Contexto: auditoría previa (hecha en la computadora de CASA, junio 2026)

Esto YA se analizó en la otra máquina. **No empieces de cero: construí sobre esto.**

**Perfil del usuario (calibración — verificá, no asumas ciego):**
- **No programa.** Claude escribe todo el código; él dirige producto y decisiones. Quiere explicaciones a
  **alto nivel de abstracción**, sin jerga, con números/analogías. ~1 de cada 3 prompts pide *entender* algo
  ("explicame", "¿qué es...?", "no entiendo"). **Las explicaciones son un entregable, no ruido.**
- **Dicta por voz.** Prompts largos (mediana ~760 chars), con varias cosas mezcladas y errores de
  transcripción de términos técnicos (ver glosario en ANEXO 1). Interpretá la intención.
- **Trabaja de noche** (pico 21h–1am, después del laburo), a veces cansado → prompts más dispersos.
- **Dos computadoras** (casa + laburo) sincronizadas por git. Esta —la de laburo— es la **más actualizada**:
  acá aprendió más cosas y trabaja mejor. Los skills/CLAUDE.md global NO viajan por el repo del proyecto.

**Números de la computadora de casa (referencia, para comparar):**
247 prompts en ~4 semanas · largo mediana 760 / promedio 1473 · 31% piden entender un concepto ·
28 señales de fricción con el entorno `.bat`/`file://` · 20 de "¿estás seguro/verificá" · 26 de plan-first ·
0 skills propios usados (solo `/compact` ×11, `/model` ×8).

**Lo que hace BIEN (mantener):** plan-first ("antes de tocar código", "modo planificación", "¿dudas?");
da el *porqué* de negocio y delega criterio; mantiene CLAUDE.md/MEMORY.md vivos; consciente del costo de API;
pide rankings; usa capturas para señalar UI. Su CLAUDE.md global es muy bueno.

**Mejoras ACTIVAS recomendadas (cómo pide):**
- A. Separar "pregunta para entender" de "acción a ejecutar": al cerrar el dictado, una línea
  `Acción ahora: <una cosa>. El resto son preguntas/ideas`.
- B. Pedir verificación objetiva (evidencia: salida de un comando, un chequeo que falle) en vez de "¿estás seguro?".
- C. Una sesión = un objetivo (cerrar y abrir nueva al cambiar de tema; el CLAUDE.md da el contexto).
- D. Conceptos que se repiten → pedir que se guarden en un GLOSARIO.md.

**Mejoras PASIVAS recomendadas (skills/config):**
1. Nota de dictado + glosario en CLAUDE.md global **(YA implementada en casa; replicar acá → ANEXO 1).**
2. Skill `/estado-proyecto`: "revisá consistencia, actualizá CLAUDE.md, estado + próximos pasos rankeados".
3. Skill `/probar-escenarios` (dashboard): él dijo *"documentá que cuando te pida pruebas de todos los
   escenarios uses esto, no te lo voy a decir"*.
4. Regla/skill para abrir el dashboard con el `.bat` (no abrir el HTML directo).
5. GLOSARIO.md vivo mantenido por Claude.

**Problema de fondo señalado:** el stack `.bat` + `file://` obliga al usuario a ser el QA de cada cambio
(Claude no puede abrir la app). Alternativa: servir con `python -m http.server` para que Claude se
autoverifique. Tratar en una sesión aparte.

---

## PARTE B — Tu tarea, Claude (en la computadora de laburo)

1. **Extraé el historial de ESTA máquina.** Corré:
   ```
   powershell -ExecutionPolicy Bypass -File "%USERPROFILE%\.claude\skills\auditar-uso-claude\extraer.ps1"
   ```
   Imprime métricas y vuelca los prompts a `%TEMP%\cc_prompts.txt`. (Si la skill no se copió, guardá el
   script del **ANEXO 2** como `extraer.ps1` y corrélo.)

2. **Leé el volcado** `%TEMP%\cc_prompts.txt`: cabecera, sesiones con más prompts, y Grep por los temas que
   marcaron alto en las métricas. No hace falta leerlo entero.

3. **Antes de recomendar crear skills, revisá lo que YA existe en esta máquina:** mirá `.claude/skills/` y
   `.claude/commands/` de cada repo (sobre todo el del dashboard). El usuario cree tener skills de
   **análisis** y **pruebas** acá — confirmalo y **NO dupliques**: si existen, evaluá si funcionan bien y
   solo proponé ajustes; si no existen, ahí sí proponé crearlas (#2/#3 de la PARTE A).

4. **Producí una auditoría que construya sobre la PARTE A** (no una nueva desde cero). Marcá explícitamente:
   **qué se confirma**, **qué cambió** y **qué es nuevo** respecto a la computadora de casa. Estructura:
   *Qué mantener / Mejoras activas / Mejoras pasivas*, rankeado por impacto, en español, **recomendá primero
   e implementá solo si el usuario aprueba**.

5. Aplicá la calibración del usuario (PARTE A): no programa, quiere alto nivel de abstracción, dicta por voz.

---

## PARTE C — Dónde guardar el resultado

Guardá la auditoría nueva en:
```
%USERPROFILE%\.claude\skills\auditar-uso-claude\auditoria-laburo.md
```
y mostrale al usuario en el chat un índice de ~5 líneas + las preguntas de aprobación de las mejoras.

---

## PARTE D — Checklist de setup manual (humano)

- [ ] Copiada la carpeta `auditar-uso-claude` a `%USERPROFILE%\.claude\skills\`.
- [ ] Agregado el ANEXO 1 (nota de dictado) al `%USERPROFILE%\.claude\CLAUDE.md` de esta máquina.
- [ ] Corrida la auditoría con el prompt de arriba.
- [ ] (después de aprobar) Creadas las skills de proyecto que falten — van en `.claude/skills/` **dentro del
      repo** así viajan por git a la otra compu.

---

## ANEXO 1 — Nota de dictado para pegar en el CLAUDE.md global

```markdown
## Dictado por voz

* Mis prompts suelen venir de dictado por voz: largos, conversacionales, con varias cosas mezcladas y errores de transcripción de términos técnicos. Interpretá la intención; si un término técnico no cierra, asumí el más probable y aclará tu interpretación en una línea.
* Glosario de transcripciones frecuentes: `cloud` / `cloud code` / `Cloud` → Claude / Claude Code · `cloud md` / `claude md` → CLAUDE.md · `punto bat` → `.bat` · `Superbase` / `SupaBase` → Supabase · `Sonett` / `Sonet` → Sonnet · `COVID` / `comitiar` → commit / commitear · `Jardines` → harness · `CEO` (cuando hablo de buscar en Google) → SEO · `dominion` → dominio · `analcisconia` / `menisconía` → análisis con IA.
* Si un prompt mezcla preguntas y acciones, antes de ejecutar confirmá en UNA línea qué vas a hacer ahora y qué quedó como pregunta/idea (no ejecutes lo que era solo una duda).
```

---

## ANEXO 2 — extraer.ps1 (por si NO copiaste la carpeta de la skill)

Guardá este bloque como `%USERPROFILE%\.claude\skills\auditar-uso-claude\extraer.ps1` y corrélo.

```powershell
param([string]$OutDir = $env:TEMP)
$base = Join-Path $env:USERPROFILE ".claude\projects"
if (-not (Test-Path $base)) { Write-Error "No existe $base"; exit 1 }
$out = Join-Path $OutDir "cc_prompts.txt"
$prompts   = New-Object System.Collections.Generic.List[object]
$commands  = New-Object System.Collections.Generic.List[string]
$interrupts = 0
Get-ChildItem -Path $base -Directory | ForEach-Object {
  $proj = $_.Name
  Get-ChildItem -Path $_.FullName -Filter *.jsonl -File | ForEach-Object {
    $sess = $_.BaseName
    $raw = Get-Content -Path $_.FullName -Encoding UTF8
    foreach ($l in $raw) {
      if ([string]::IsNullOrWhiteSpace($l)) { continue }
      try { $o = $l | ConvertFrom-Json } catch { continue }
      if ($o.type -ne 'user') { continue }
      $msg = $o.message
      if ($null -eq $msg -or $msg.role -ne 'user') { continue }
      $content = $msg.content
      $texts = @()
      if ($content -is [string]) { $texts += $content }
      else { foreach ($item in $content) { if ($item.type -eq 'text' -and $item.text) { $texts += $item.text } } }
      foreach ($t in $texts) {
        if ($t -match '<command-name>([^<]+)</command-name>') { $commands.Add($matches[1]) }
        $tt = $t.Trim()
        if ($tt -eq '') { continue }
        if ($tt.StartsWith('[Request interrupted')) { $interrupts++; continue }
        if ($tt.StartsWith('<command-'))     { continue }
        if ($tt.StartsWith('<local-command')) { continue }
        if ($tt.StartsWith('<system-reminder')) { continue }
        if ($tt.StartsWith('Caveat:'))       { continue }
        if ($tt.StartsWith('<task-notification>')) { continue }
        $prompts.Add([PSCustomObject]@{ project=$proj; session=$sess; ts=$o.timestamp; len=$tt.Length; text=$tt })
      }
    }
  }
}
$sb = New-Object System.Text.StringBuilder
$grouped = $prompts | Group-Object session
foreach ($g in $grouped) {
  [void]$sb.AppendLine("######## SESSION $($g.Name) [$($g.Group[0].project)] ($($g.Count) prompts) ########")
  foreach ($p in $g.Group) { [void]$sb.AppendLine("---[$($p.ts)] (len=$($p.len))"); [void]$sb.AppendLine($p.text) }
  [void]$sb.AppendLine("")
}
[System.IO.File]::WriteAllText($out, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
$lens = @($prompts | ForEach-Object { $_.len } | Sort-Object)
$n = $lens.Count
if ($n -eq 0) { Write-Output "Sin prompts."; exit 0 }
$median = $lens[[int][math]::Floor($n/2)]
$avg = [math]::Round(($lens | Measure-Object -Average).Average,0)
$buckets = [ordered]@{
  'friccion/correccion'   = 'no funciona|no anda|sigue (sin|igual|mal)|esta mal|no era|rompiste|otra vez|de nuevo|te dije|ya te (dije|ped)|por que no|no pasa nada|se cierra'
  'duda/verificacion'     = 'estas seguro|verific|fijate si|comprob|funciona\?|asegurate|cheque|proba si|revisa si'
  'comprension/ensename'  = 'no entiendo|no se que|explicame|no me queda claro|que significa|en simple|mas facil|hiperbasic|abstraccion|que es '
  'entorno bat/local'     = '\.bat|cmd|file://|doble clic|servidor local|localhost|punto bat|abrir el dashboard'
  'plan-first/preguntar'  = 'antes de tocar|antes de empezar|modo planific|mostrame el plan|tenes alguna duda|no edites|pregunta(me|r) antes|planifica'
  'docs/contexto'         = 'cloud ?md|claude ?md|memory|documenta|actualiza.*md|estado del proyecto'
}
$bucketCounts = [ordered]@{}
foreach ($k in $buckets.Keys) { $rx = $buckets[$k]; $bucketCounts[$k] = ($prompts | Where-Object { $_.text -match "(?i)$rx" }).Count }
$dts = $prompts | ForEach-Object { try { [datetime]::Parse($_.ts).ToLocalTime() } catch {} }
$minD = ($dts | Measure-Object -Minimum).Minimum; $maxD = ($dts | Measure-Object -Maximum).Maximum
$byHour = $dts | Group-Object { $_.Hour } | Sort-Object { [int]$_.Name }
Write-Output "================ AUDITORIA DE USO - METRICAS ================"
Write-Output "Volcado: $out"
Write-Output "Total prompts: $n"
Write-Output "Largo -> promedio: $avg  mediana: $median  max: $($lens[-1])"
Write-Output "Interrupciones: $interrupts"
Write-Output "Rango temporal: $minD -> $maxD"
Write-Output "`n--- Buckets de largo (chars) ---"
$prompts | Group-Object { if($_.len -lt 40){'0-39'} elseif($_.len -lt 120){'40-119'} elseif($_.len -lt 300){'120-299'} elseif($_.len -lt 800){'300-799'} else {'800+'} } | Sort-Object Name | ForEach-Object { Write-Output ("  {0,-8} {1}" -f $_.Name, $_.Count) }
Write-Output "`n--- Senales por tema ---"
foreach ($k in $bucketCounts.Keys) { Write-Output ("  {0,-22} {1}" -f $k, $bucketCounts[$k]) }
Write-Output "`n--- Slash commands ---"
if ($commands.Count -gt 0) { $commands | Group-Object | Sort-Object Count -Descending | ForEach-Object { Write-Output ("  {0,-14} {1}" -f $_.Name, $_.Count) } } else { Write-Output "  (ninguno)" }
Write-Output "`n--- Prompts por sesion (top 8) ---"
$grouped | Select-Object Count,Name | Sort-Object Count -Descending | Select-Object -First 8 | ForEach-Object { Write-Output ("  {0,3}  {1}" -f $_.Count, $_.Name) }
Write-Output "`n--- Actividad por hora (local) ---"
foreach ($h in $byHour) { Write-Output ("  {0,2}h  {1}" -f $h.Name, $h.Count) }
Write-Output "`n--- Por proyecto ---"
$prompts | Group-Object project | Sort-Object Count -Descending | ForEach-Object { Write-Output ("  {0,4}  {1}" -f $_.Count, $_.Name) }
```
