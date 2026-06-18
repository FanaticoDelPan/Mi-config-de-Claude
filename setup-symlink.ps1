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
