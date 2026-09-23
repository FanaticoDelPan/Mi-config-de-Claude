# Guarda un secreto (clave, token, contrasena) en el .env del proyecto SIN mostrarlo.
#
# Para que sirve: pasarle un secreto a Claude sin pegarlo en el chat (queda en el
# historial) ni dejarlo en un TXT del escritorio (OneDrive lo sube a la nube).
#
# Como se usa:
#   1. Copias el secreto (Ctrl+C) desde donde lo tengas.
#   2. Desde la carpeta del proyecto se corre:
#        powershell -NoProfile -File <este-repo>\guardar-secreto.ps1 NOMBRE_VARIABLE
#      (o -Archivo .env para elegir el archivo; por defecto usa .env.local si existe,
#      si no .env si existe, y si no hay ninguno crea .env.local).
#
# Que hace: lee el portapapeles, escribe NOMBRE=valor en el archivo (reemplaza la
# linea si ya estaba), vacia el portapapeles y avisa si el archivo NO esta excluido
# de git. Nunca imprime el valor: solo cuantos caracteres tiene.

param(
    [Parameter(Mandatory = $true, Position = 0)][string]$Nombre,
    [string]$Archivo
)

$ErrorActionPreference = 'Stop'

if ($Nombre -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') {
    throw "Nombre de variable invalido: '$Nombre'. Solo letras, numeros y guion bajo, sin empezar con numero."
}

if (-not $Archivo) {
    if (Test-Path '.env.local') { $Archivo = '.env.local' }
    elseif (Test-Path '.env') { $Archivo = '.env' }
    else { $Archivo = '.env.local' }
}
$ruta = Join-Path (Get-Location) $Archivo

$valor = Get-Clipboard -Raw
if ($null -ne $valor) { $valor = $valor.Trim() }
if ([string]::IsNullOrEmpty($valor)) { throw 'El portapapeles esta vacio: copia el secreto y volve a correrlo.' }
if ($valor -match "[`r`n]") { throw 'El portapapeles tiene varias lineas: este script solo guarda secretos de una linea.' }

$lineas = @()
if (Test-Path $ruta) { $lineas = @([System.IO.File]::ReadAllLines($ruta)) }

$nueva = "$Nombre=$valor"
$prefijo = "$Nombre="
$reemplazada = $false
for ($i = 0; $i -lt $lineas.Count; $i++) {
    if ($lineas[$i].StartsWith($prefijo)) { $lineas[$i] = $nueva; $reemplazada = $true }
}
if (-not $reemplazada) { $lineas += $nueva }

[System.IO.File]::WriteAllLines($ruta, [string[]]$lineas, (New-Object System.Text.UTF8Encoding($false)))

# Vaciar el portapapeles.
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Clipboard]::Clear()

$accion = if ($reemplazada) { 'reemplazado' } else { 'agregado' }
Write-Output "OK: $Nombre $accion en $Archivo ($($valor.Length) caracteres). Portapapeles vaciado."
Write-Output "Si usas el historial del portapapeles (Win+V), borra ahi la entrada a mano."

# Avisar si el archivo no esta excluido de git (se subiria al repo con el proximo commit).
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    & git rev-parse --is-inside-work-tree 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        & git check-ignore -q -- $Archivo
        if ($LASTEXITCODE -ne 0) {
            Write-Output "ATENCION: $Archivo NO esta en el .gitignore: el secreto se subiria con el proximo commit. Agregalo antes de commitear."
            exit 2
        }
    }
}
exit 0
