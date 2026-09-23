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

# --- Skills: ~/.claude/skills pasa a ser un junction a la carpeta skills de este repo ---
# Un junction es un link de carpeta que NO pide admin. Si ya habia una carpeta real con
# skills, las que el repo no tenga se mueven al repo (asi se suben con el proximo commit)
# y lo que quede se respalda como skills.backup.
$repoSkills   = Join-Path $PSScriptRoot 'skills'
$globalSkills = Join-Path $globalDir 'skills'
if (-not (Test-Path $repoSkills)) { New-Item -ItemType Directory -Path $repoSkills | Out-Null }

$skillsAtado = $false
if (Test-Path $globalSkills) {
    $gs = Get-Item $globalSkills -Force
    if ($gs.LinkType -in @('Junction', 'SymbolicLink')) {
        $gt = @($gs.Target)[0]
        if ((Test-Path $gt) -and ((Resolve-Path $gt).Path -eq (Resolve-Path $repoSkills).Path)) {
            $skillsAtado = $true
        } else {
            $gs.Delete()   # borra solo el link, no la carpeta a la que apuntaba
        }
    } else {
        foreach ($d in @(Get-ChildItem $globalSkills -Directory)) {
            $dest = Join-Path $repoSkills $d.Name
            if (-not (Test-Path $dest)) {
                Move-Item $d.FullName $dest
                Write-Host "Skill '$($d.Name)' movida al repo." -ForegroundColor Yellow
            }
        }
        if (@(Get-ChildItem $globalSkills -Force).Count -eq 0) {
            [System.IO.Directory]::Delete($globalSkills)
        } else {
            $skillsBackup = Join-Path $globalDir 'skills.backup'
            Rename-Item $globalSkills $skillsBackup
            Write-Host "Quedaron cosas en ~/.claude/skills que el repo ya tenia: respaldadas en $skillsBackup" -ForegroundColor Yellow
        }
    }
}
if ($skillsAtado) {
    Write-Host "OK -> ~/.claude/skills ya apunta a este repo." -ForegroundColor Green
} else {
    New-Item -ItemType Junction -Path $globalSkills -Target $repoSkills | Out-Null
    Write-Host "OK -> ~/.claude/skills apunta a $repoSkills" -ForegroundColor Green
}

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
