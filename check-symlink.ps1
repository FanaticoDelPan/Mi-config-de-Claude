# Verifica que el symlink global ~/.claude/CLAUDE.md este sano:
#   1. que exista,
#   2. que sea un symlink (no un archivo suelto o un hardlink),
#   3. que su destino exista (se rompe si renombras/moves la carpeta del repo),
#   4. que apunte al CLAUDE.md de ESTE repo.
#
# No necesita admin: solo lee, no crea nada. Si algo esta mal, avisa y dice
# como arreglarlo (siempre: correr .\setup-symlink.ps1).
#
# Uso manual:  .\check-symlink.ps1
# Tambien sirve para enchufarlo a un hook SessionStart de Claude Code.
#
# Devuelve exit code 0 si esta todo bien, 1 si hay algo para arreglar.
#
# -Quiet : no imprime el mensaje de exito (solo avisa si hay un problema).
#          Lo usa el hook automatico para no ensuciar cada sesion con un "OK".

param([switch]$Quiet)

$globalFile = Join-Path $env:USERPROFILE '.claude\CLAUDE.md'
$repoFile   = Join-Path $PSScriptRoot 'CLAUDE.md'

function Aviso($msg) { Write-Host "[CLAUDE.md] $msg" -ForegroundColor Yellow }

# 1. Existe algo en el global?
if (-not (Test-Path $globalFile)) {
    Aviso "No existe ~/.claude/CLAUDE.md -> el CLAUDE.md global NO se esta cargando."
    Aviso "Arreglalo con:  .\setup-symlink.ps1"
    exit 1
}

$item = Get-Item $globalFile -Force

# 2. Es un symlink?
if ($item.LinkType -ne 'SymbolicLink') {
    $kind = if ($item.LinkType) { $item.LinkType } else { 'archivo real' }
    Aviso "~/.claude/CLAUDE.md existe pero NO es un symlink (es: $kind)."
    Aviso "Puede desincronizarse del repo. Recrealo con:  .\setup-symlink.ps1"
    exit 1
}

# 3. El destino al que apunta sigue existiendo?
$target = @($item.Target)[0]
if (-not (Test-Path $target)) {
    Aviso "El symlink esta ROTO: apunta a '$target' que ya no existe."
    Aviso "(Tipico si renombraste o moviste la carpeta del repo.)"
    Aviso "Arreglalo con:  .\setup-symlink.ps1"
    exit 1
}

# 4. Apunta al CLAUDE.md de este mismo repo?
if ((Resolve-Path $target).Path -ne (Resolve-Path $repoFile).Path) {
    Aviso "El symlink resuelve, pero apunta a OTRO CLAUDE.md:"
    Aviso "  apunta a:  $target"
    Aviso "  este repo: $repoFile"
    Aviso "Si queres que apunte aca, corre:  .\setup-symlink.ps1"
    exit 1
}

if (-not $Quiet) {
    Write-Host "[CLAUDE.md] OK -> symlink sano apuntando a $target" -ForegroundColor Green
}
exit 0
