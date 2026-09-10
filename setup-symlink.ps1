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

# Escribir sin BOM (los parsers de JSON no toleran el BOM).
$json = $settings | ConvertTo-Json -Depth 12
[System.IO.File]::WriteAllText($settingsFile, $json)
Write-Host "OK -> hook SessionStart registrado -> $checkScript" -ForegroundColor Green
