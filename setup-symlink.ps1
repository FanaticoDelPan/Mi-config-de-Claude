# Crea (o recrea) el symlink ~/.claude/CLAUDE.md -> el CLAUDE.md de este repo.
# Asi, editar el global y editar el del repo es lo mismo: un solo archivo.
#
# Requisitos: correr esta terminal COMO ADMINISTRADOR, o tener el Modo
# Desarrollador activado (Configuracion -> Privacidad y seguridad -> Para programadores).
#
# Uso: clic derecho -> "Ejecutar con PowerShell", o desde una terminal:  .\setup-symlink.ps1

$ErrorActionPreference = 'Stop'

# El destino del link es el CLAUDE.md que esta al lado de este script,
# asi funciona sin importar en que ruta hayas clonado el repo.
$repoFile   = Join-Path $PSScriptRoot 'CLAUDE.md'
$globalDir  = Join-Path $env:USERPROFILE '.claude'
$globalFile = Join-Path $globalDir 'CLAUDE.md'

if (-not (Test-Path $repoFile)) { throw "No encuentro CLAUDE.md en el repo ($repoFile)." }
if (-not (Test-Path $globalDir)) { New-Item -ItemType Directory -Path $globalDir | Out-Null }

# Si ya hay algo en el global, decidir que hacer.
if (Test-Path $globalFile) {
    $item = Get-Item $globalFile -Force
    if ($item.LinkType -eq 'SymbolicLink') {
        Write-Host "Ya existia un symlink (-> $($item.Target)). Lo recreo apuntando a este repo."
        Remove-Item $globalFile -Force
    } else {
        $backup = "$globalFile.backup"
        Write-Host "Habia un CLAUDE.md real. Lo respaldo en: $backup" -ForegroundColor Yellow
        Move-Item $globalFile $backup -Force
    }
}

try {
    New-Item -ItemType SymbolicLink -Path $globalFile -Target $repoFile | Out-Null
} catch {
    Write-Host "ERROR: no se pudo crear el symlink." -ForegroundColor Red
    Write-Host "Solucion: corre esta terminal como Administrador, o activa el Modo Desarrollador." -ForegroundColor Yellow
    throw
}

$check = Get-Item $globalFile -Force
if ($check.LinkType -eq 'SymbolicLink') {
    Write-Host "OK -> $globalFile apunta a $($check.Target)" -ForegroundColor Green
} else {
    throw "Algo salio mal: el global no quedo como symlink."
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
