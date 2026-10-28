# Deja la PC lista para que la PROXIMA caida del Explorador guarde un volcado que Claude pueda abrir,
# y copia los informes de las caidas anteriores (que Windows guarda solo para administradores) a una
# carpeta del usuario. Sin el volcado solo se sabe DONDE se cae el Explorador, no QUIEN lo provoca.
#
# Corre COMO ADMINISTRADOR (lo pide solo si hace falta). Deshacer: el mismo script con -Deshacer.
# Volcados e informes quedan en %LOCALAPPDATA%\CrashDumps\explorer. Cada volcado pesa cientos de MB:
# se guardan los 3 ultimos y se borran a mano una vez analizados.
param([switch]$Deshacer)

$esAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $esAdmin) {
    $args2 = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"")
    if ($Deshacer) { $args2 += '-Deshacer' }
    Start-Process powershell -Verb RunAs -ArgumentList $args2
    return
}

$clave = 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\explorer.exe'
$destino = Join-Path $env:LOCALAPPDATA 'CrashDumps\explorer'

if ($Deshacer) {
    if (Test-Path $clave) { Remove-Item -Path $clave -Recurse }
    Write-Host 'Listo: el Explorador ya no guarda volcados. Los que ya estan siguen en' $destino
    Read-Host 'Enter para cerrar'
    return
}

New-Item -ItemType Directory -Force -Path $destino | Out-Null
New-Item -Path $clave -Force | Out-Null
Set-ItemProperty -Path $clave -Name DumpFolder -Value $destino -Type ExpandString
Set-ItemProperty -Path $clave -Name DumpType -Value 2 -Type DWord      # 2 = completo
Set-ItemProperty -Path $clave -Name DumpCount -Value 3 -Type DWord

$archivo = Join-Path $env:ProgramData 'Microsoft\Windows\WER\ReportArchive'
$informes = Join-Path $destino 'informes'
New-Item -ItemType Directory -Force -Path $informes | Out-Null
$carpetas = Get-ChildItem $archivo -Directory -ErrorAction SilentlyContinue |
    Where-Object Name -like 'AppCrash_Explorer.EXE*' | Sort-Object LastWriteTime -Descending | Select-Object -First 15
foreach ($c in $carpetas) {
    Copy-Item -Path $c.FullName -Destination $informes -Recurse -Force
}
# Las copias heredan los permisos de la carpeta del usuario: quedan legibles sin ser administrador.

Write-Host "Listo. Proxima caida del Explorador -> volcado en $destino"
Write-Host "Informes anteriores copiados: $($carpetas.Count)"
Read-Host 'Enter para cerrar'
