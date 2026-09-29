# Crea (o recrea) el symlink ~/.claude/CLAUDE.md -> el CLAUDE.md de este repo.
# Asi, editar el global y editar el del repo es lo mismo: un solo archivo.
#
# Requisitos: correr esta terminal COMO ADMINISTRADOR, o tener el Modo
# Desarrollador activado (Configuracion -> Privacidad y seguridad -> Para programadores).
#
# Uso: clic derecho -> "Ejecutar con PowerShell", o desde una terminal:  .\setup-symlink.ps1

$ErrorActionPreference = 'Stop'

# El destino esta al lado de este script, asi funciona sin importar en que ruta hayas
# clonado el repo.
#
# OJO: el symlink es SOLO para el CLAUDE.md, que es el que el harness tiene que cargar
# solo desde ~/.claude. El otro archivo del repo -- entorno-windows.md, las trampas de la
# maquina -- NO se enlaza: el CLAUDE.md lo cita por su ruta en el repo. Crear un symlink
# exige privilegios de administrador, y hacer que LEER una nota dependa de una corrida
# elevada es cambiarle un problema por otro peor: si el enlace falta, el puntero apunta a
# la nada y las trampas vuelven a morder en silencio. Apuntando al repo, no hay nada que
# instalar y es imposible que se desincronice.
$globalDir = Join-Path $env:USERPROFILE '.claude'
if (-not (Test-Path $globalDir)) { New-Item -ItemType Directory -Path $globalDir | Out-Null }

function Enlazar ([string]$nombre) {
    $repoFile   = Join-Path $PSScriptRoot $nombre
    $globalFile = Join-Path $globalDir $nombre

    if (-not (Test-Path $repoFile)) { throw "No encuentro $nombre en el repo ($repoFile)." }

    # Si ya apunta a este repo no se toca: asi el script se re-corre sin admin para
    # actualizar skills y settings.
    if (Test-Path $globalFile) {
        $prev = Get-Item $globalFile -Force
        $pt = @($prev.Target)[0]
        if ($prev.LinkType -eq 'SymbolicLink' -and $pt -and (Test-Path $pt) -and
            ((Resolve-Path $pt).Path -eq (Resolve-Path $repoFile).Path)) {
            Write-Host "OK -> $nombre ya apunta a este repo; no lo toco." -ForegroundColor Green
            return
        }
    }

    # Si ya hay algo en el global, decidir que hacer.
    if (Test-Path $globalFile) {
        $item = Get-Item $globalFile -Force
        if ($item.LinkType -eq 'SymbolicLink') {
            Write-Host "$nombre ya era un symlink (-> $($item.Target)). Lo recreo apuntando a este repo."
            Remove-Item $globalFile -Force
        } else {
            $backup = "$globalFile.backup"
            Write-Host "Habia un $nombre real. Lo respaldo en: $backup" -ForegroundColor Yellow
            Move-Item $globalFile $backup -Force
        }
    }

    try {
        New-Item -ItemType SymbolicLink -Path $globalFile -Target $repoFile | Out-Null
    } catch {
        Write-Host "ERROR: no se pudo crear el symlink de $nombre." -ForegroundColor Red
        Write-Host "Solucion: corre esta terminal como Administrador, o activa el Modo Desarrollador." -ForegroundColor Yellow
        throw
    }

    $check = Get-Item $globalFile -Force
    if ($check.LinkType -ne 'SymbolicLink') { throw "Algo salio mal: $nombre no quedo como symlink." }
    Write-Host "OK -> $globalFile apunta a $($check.Target)" -ForegroundColor Green
}

Enlazar 'CLAUDE.md'

# El otro archivo no se enlaza, pero si tiene que ESTAR: el CLAUDE.md manda leerlo antes de
# tocar la consola y lo cita por esta ruta.
$entorno = Join-Path $PSScriptRoot 'entorno-windows.md'
if (Test-Path $entorno) {
    Write-Host "OK -> las notas de entorno estan en $entorno (el CLAUDE.md las cita por esa ruta)." -ForegroundColor Green
} else {
    Write-Host "AVISO: falta entorno-windows.md en el repo. El CLAUDE.md lo cita y no lo va a encontrar." -ForegroundColor Yellow
}

# --- Skills: un junction POR SKILL adentro de ~/.claude/skills, no la carpeta entera ---
# ~/.claude/skills es compartida con la app: ahi guarda su propia copia de las skills de
# Anthropic (la carpeta 'synced', que baja sola en cada maquina). Atar la carpeta entera al
# repo metia esa copia en git, asi que la carpeta queda REAL y adentro va un junction (link de
# carpeta, no pide admin) por cada skill del repo.
# Skill nuestra = carpeta con SKILL.md directo adentro. Lo que no lo tenga es de la app y no
# se toca. Una skill creada en esta maquina (carpeta real con SKILL.md) se mueve al repo, asi
# se sube con el proximo commit.
$repoSkills   = Join-Path $PSScriptRoot 'skills'
$globalSkills = Join-Path $globalDir 'skills'
if (-not (Test-Path $repoSkills)) { New-Item -ItemType Directory -Path $repoSkills | Out-Null }

function Es-Skill ($dir) { Test-Path -LiteralPath (Join-Path $dir.FullName 'SKILL.md') }

# Esquema viejo (la carpeta entera como junction al repo): se borra solo el link, y lo que la
# app haya dejado adentro del repo por ese link vuelve a ~/.claude/skills.
if (Test-Path $globalSkills) {
    $gs = Get-Item $globalSkills -Force
    if ($gs.LinkType -in @('Junction', 'SymbolicLink')) {
        $gs.Delete()   # borra solo el link, no la carpeta a la que apuntaba
        Write-Host "~/.claude/skills era un link a la carpeta entera: paso a un link por skill." -ForegroundColor Yellow
    }
}
if (-not (Test-Path $globalSkills)) { New-Item -ItemType Directory -Path $globalSkills | Out-Null }
# Lo versionado no se mueve nunca. try: con 'Stop', el stderr de git (p. ej. copia sin .git) corta el script.
$versionado = @()
try { $versionado = @(& git -C $PSScriptRoot ls-files -- skills 2>$null) } catch { }
foreach ($d in @(Get-ChildItem $repoSkills -Directory -Force)) {
    if (Es-Skill $d) { continue }
    if (@($versionado -like "skills/$($d.Name)/*").Count -gt 0) { continue }
    $dest = Join-Path $globalSkills $d.Name
    if (-not (Test-Path $dest)) {
        Move-Item $d.FullName $dest
        Write-Host "'$($d.Name)' no es una skill nuestra (es de la app): vuelve a ~/.claude/skills." -ForegroundColor Yellow
    }
}

# Skills creadas en esta maquina -> al repo. Si el repo ya tiene una con ese nombre, gana la
# del repo y la local se respalda FUERA de skills (adentro la app la cargaria como otra skill).
foreach ($d in @(Get-ChildItem $globalSkills -Directory -Force)) {
    if ($d.LinkType -or -not (Es-Skill $d)) { continue }
    $dest = Join-Path $repoSkills $d.Name
    if (Test-Path $dest) {
        $skillsBackup = Join-Path $globalDir 'skills.backup'
        if (-not (Test-Path $skillsBackup)) { New-Item -ItemType Directory -Path $skillsBackup | Out-Null }
        $bk = Join-Path $skillsBackup ($d.Name + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
        Move-Item $d.FullName $bk
        Write-Host "Skill '$($d.Name)' ya estaba en el repo: la copia local quedo respaldada en $bk" -ForegroundColor Yellow
    } else {
        Move-Item $d.FullName $dest
        Write-Host "Skill '$($d.Name)' movida al repo (se sube con el proximo commit)." -ForegroundColor Yellow
    }
}

# Links que ya no sirven: rotos (la skill se borro o se renombro en el repo) o apuntando a otro lado.
foreach ($d in @(Get-ChildItem $globalSkills -Directory -Force)) {
    if (-not $d.LinkType) { continue }
    $t = @($d.Target)[0]
    $propio = Join-Path $repoSkills $d.Name
    if (-not ($t -and (Test-Path $t) -and (Test-Path $propio) -and
              ((Resolve-Path $t).Path -eq (Resolve-Path $propio).Path))) {
        $d.Delete()
    }
}

$atadas = @()
foreach ($d in @(Get-ChildItem $repoSkills -Directory -Force)) {
    if (-not (Es-Skill $d)) { continue }
    $link = Join-Path $globalSkills $d.Name
    if (-not (Test-Path $link)) { New-Item -ItemType Junction -Path $link -Target $d.FullName | Out-Null }
    $atadas += $d.Name
}
Write-Host "OK -> skills del repo atadas en ~/.claude/skills: $(if ($atadas) { $atadas -join ', ' } else { '(ninguna)' })" -ForegroundColor Green

# --- Registrar el hook que corre check-symlink.ps1 solo en cada sesion ---
# La ruta NO queda fija a mano: se calcula desde donde vive el repo en ESTA
# maquina ($PSScriptRoot) y se escribe en el settings.json de esta maquina.
# Asi, clonar el repo en cualquier ruta + correr este script deja el hook
# apuntando al lugar correcto, sin editar nada a mano.
$settingsFile = Join-Path $globalDir 'settings.json'
$checkScript  = Join-Path $PSScriptRoot 'check-symlink.ps1'
$hookCmd      = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$checkScript`" -Quiet"

if (Test-Path $settingsFile) {
    try { $settings = Get-Content $settingsFile -Raw | ConvertFrom-Json }
    catch { throw "settings.json existe pero no es JSON valido: $settingsFile" }
} else {
    $settings = [pscustomobject]@{}
}

# Asegurar la rama hooks.SessionStart sin pisar otras settings que ya tengas.
if (-not ($settings.PSObject.Properties.Name -contains 'hooks')) {
    $settings | Add-Member -NotePropertyName 'hooks' -NotePropertyValue ([pscustomobject]@{})
}
if (-not ($settings.hooks.PSObject.Properties.Name -contains 'SessionStart')) {
    $settings.hooks | Add-Member -NotePropertyName 'SessionStart' -NotePropertyValue @()
}

# Sacar cualquier registro previo de check-symlink.ps1 (evita duplicados y
# corrige la ruta si moviste el repo), conservando el resto de tus hooks.
$kept = @()
foreach ($group in @($settings.hooks.SessionStart)) {
    $refsCheck = $false
    foreach ($h in @($group.hooks)) {
        if ($h.command -and $h.command -match 'check-symlink\.ps1') { $refsCheck = $true }
    }
    if (-not $refsCheck) { $kept += $group }
}

$newGroup = [pscustomobject]@{
    hooks = @( [pscustomobject]@{ type = 'command'; command = $hookCmd } )
}
$settings.hooks.SessionStart = @($kept) + $newGroup

# Conservar el historial de conversaciones ~10 anos. Por defecto Claude Code borra las
# conversaciones de mas de 30 dias, y con ellas se fue el historial de un proyecto entero.
$diasHistorial = 3650
if ($settings.PSObject.Properties.Name -contains 'cleanupPeriodDays') {
    $settings.cleanupPeriodDays = $diasHistorial
} else {
    $settings | Add-Member -NotePropertyName 'cleanupPeriodDays' -NotePropertyValue $diasHistorial
}

# Escribir sin BOM (los parsers de JSON no toleran el BOM).
$json = $settings | ConvertTo-Json -Depth 12
[System.IO.File]::WriteAllText($settingsFile, $json)
Write-Host "OK -> hook SessionStart registrado -> $checkScript" -ForegroundColor Green
