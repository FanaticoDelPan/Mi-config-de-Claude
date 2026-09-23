# Extrae todos los prompts del usuario del historial de Claude Code y calcula metricas.
# Portable: funciona en cualquier maquina Windows con el historial en ~/.claude/projects.
# Uso:  powershell -File extraer.ps1            (vuelca a $env:TEMP\cc_prompts.txt)
#       powershell -File extraer.ps1 -OutDir C:\ruta
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

# Volcado para lectura
$sb = New-Object System.Text.StringBuilder
$grouped = $prompts | Group-Object session
foreach ($g in $grouped) {
  [void]$sb.AppendLine("######## SESSION $($g.Name) [$($g.Group[0].project)] ($($g.Count) prompts) ########")
  foreach ($p in $g.Group) { [void]$sb.AppendLine("---[$($p.ts)] (len=$($p.len))"); [void]$sb.AppendLine($p.text) }
  [void]$sb.AppendLine("")
}
[System.IO.File]::WriteAllText($out, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))

# Metricas
$lens = @($prompts | ForEach-Object { $_.len } | Sort-Object)
$n = $lens.Count
if ($n -eq 0) { Write-Output "Sin prompts. Nada que analizar."; exit 0 }
$median = $lens[[int][math]::Floor($n/2)]
$avg = [math]::Round(($lens | Measure-Object -Average).Average,0)

# Buckets de palabras clave (a nivel prompt) - editables segun el usuario
$buckets = [ordered]@{
  'friccion/correccion'   = 'no funciona|no anda|sigue (sin|igual|mal)|esta mal|no era|rompiste|otra vez|de nuevo|te dije|ya te (dije|ped)|por que no|no pasa nada|se cierra'
  'duda/verificacion'     = 'estas seguro|verific|fijate si|comprob|funciona\?|asegurate|cheque|proba si|revisa si'
  'comprension/ensename'  = 'no entiendo|no se que|explicame|no me queda claro|que significa|en simple|mas facil|hiperbasic|abstraccion|que es '
  'entorno bat/local'     = '\.bat|cmd|file://|doble clic|servidor local|localhost|punto bat|abrir el dashboard'
  'plan-first/preguntar'  = 'antes de tocar|antes de empezar|modo planific|mostrame el plan|tenes alguna duda|no edites|pregunta(me|r) antes|planifica'
  'docs/contexto'         = 'cloud ?md|claude ?md|memory|documenta|actualiza.*md|estado del proyecto'
}
$bucketCounts = [ordered]@{}
foreach ($k in $buckets.Keys) {
  $rx = $buckets[$k]
  $c = ($prompts | Where-Object { $_.text -match "(?i)$rx" }).Count
  $bucketCounts[$k] = $c
}

# Rango temporal y franja horaria (hora local)
$dts = $prompts | ForEach-Object { try { [datetime]::Parse($_.ts).ToLocalTime() } catch {} }
$minD = ($dts | Measure-Object -Minimum).Minimum
$maxD = ($dts | Measure-Object -Maximum).Maximum
$byHour = $dts | Group-Object { $_.Hour } | Sort-Object { [int]$_.Name }

Write-Output "================ AUDITORIA DE USO - METRICAS ================"
Write-Output "Volcado de prompts: $out"
Write-Output "Total prompts: $n"
Write-Output "Largo  -> promedio: $avg   mediana: $median   max: $($lens[-1])"
Write-Output "Interrupciones (Request interrupted by user): $interrupts"
Write-Output "Rango temporal: $minD  ->  $maxD"
Write-Output ""
Write-Output "--- Buckets de largo (chars) ---"
$prompts | Group-Object { if($_.len -lt 40){'0-39'} elseif($_.len -lt 120){'40-119'} elseif($_.len -lt 300){'120-299'} elseif($_.len -lt 800){'300-799'} else {'800+'} } | Sort-Object Name | ForEach-Object { Write-Output ("  {0,-8} {1}" -f $_.Name, $_.Count) }
Write-Output ""
Write-Output "--- Senales por tema (conteo de prompts que matchean) ---"
foreach ($k in $bucketCounts.Keys) { Write-Output ("  {0,-22} {1}" -f $k, $bucketCounts[$k]) }
Write-Output ""
Write-Output "--- Slash commands usados ---"
if ($commands.Count -gt 0) { $commands | Group-Object | Sort-Object Count -Descending | ForEach-Object { Write-Output ("  {0,-14} {1}" -f $_.Name, $_.Count) } } else { Write-Output "  (ninguno)" }
Write-Output ""
Write-Output "--- Prompts por sesion (top 8) ---"
$grouped | Select-Object Count,Name | Sort-Object Count -Descending | Select-Object -First 8 | ForEach-Object { Write-Output ("  {0,3}  {1}" -f $_.Count, $_.Name) }
Write-Output ""
Write-Output "--- Actividad por hora (local) ---"
foreach ($h in $byHour) { Write-Output ("  {0,2}h  {1}" -f $h.Name, $h.Count) }
Write-Output ""
Write-Output "--- Por proyecto ---"
$prompts | Group-Object project | Sort-Object Count -Descending | ForEach-Object { Write-Output ("  {0,4}  {1}" -f $_.Count, $_.Name) }
