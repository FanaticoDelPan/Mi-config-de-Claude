<#
Registro liviano del consumo de la PC, para tener historia (Windows no la guarda por programa).

Cada corrida agrega UNA fila al CSV del día con: trabajo real del procesador, velocidad efectiva
respecto de la nominal (muestra el tope de 15 W), RAM, memoria comprometida (RAM + archivo de
paginación) y procesador/RAM por FAMILIA de programas. El procesador por familia es el PROMEDIO del
intervalo desde la corrida anterior (no una foto): compara el tiempo de CPU acumulado de cada proceso.
Lo que nació y murió entre dos corridas no se ve (pierde, por ejemplo, tests muy cortos).

Una sola consulta de procesos por corrida; la columna costo_registro_s anota el CPU que gastó el
propio registro, para poder probar que no pesa.

Uso:
  registrar-consumo-pc.ps1                 -> anota una fila (lo que corre la tarea programada)
  registrar-consumo-pc.ps1 -Instalar [-Hasta 'AAAA-MM-DD HH:mm']  -> programa la tarea cada 5 min
  registrar-consumo-pc.ps1 -Desinstalar    -> borra la tarea (los CSV quedan)
Datos: %USERPROFILE%\registro-consumo-pc\consumo-AAAA-MM-DD.csv
#>
param(
    [switch]$Instalar,
    [switch]$Desinstalar,
    [string]$Hasta = ''
)

$ErrorActionPreference = 'Stop'
$nombreTarea = 'registro-consumo-pc'
# NO en AppData: la app de Claude es un paquete MSIX y lo que escribe un comando lanzado desde ella en AppData
# va a una copia privada del paquete; la tarea programada escribiría en otro archivo que Claude no ve.
$carpeta = Join-Path $env:USERPROFILE 'registro-consumo-pc'
# La tarea corre sin ventana: un error que nadie ve se anota acá.
trap {
    New-Item -ItemType Directory -Force $carpeta | Out-Null
    Add-Content (Join-Path $carpeta 'errores.log') ("{0} {1} | {2}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $_, $_.InvocationInfo.PositionMessage)
    exit 1
}

if ($Desinstalar) {
    Unregister-ScheduledTask -TaskName $nombreTarea -Confirm:$false
    "Tarea borrada. Los datos quedan en $carpeta"
    return
}

if ($Instalar) {
    # El .vbs de al lado lo lanza SIN ventana (no parpadea cada 5 minutos); la sesión S4U, que tampoco abre
    # ventana, pide administrador.
    $wscript = Join-Path $env:SystemRoot 'System32\wscript.exe'
    $vbs = [IO.Path]::ChangeExtension($PSCommandPath, '.vbs')
    $accion = New-ScheduledTaskAction -Execute $wscript -Argument "//B //Nologo `"$vbs`""
    $inicio = (Get-Date).AddMinutes(1)
    $fin = if ($Hasta) { [datetime]::ParseExact($Hasta, 'yyyy-MM-dd HH:mm', $null) } else { $inicio.AddDays(2) }
    $disparo = New-ScheduledTaskTrigger -Once -At $inicio -RepetitionInterval (New-TimeSpan -Minutes 5) `
        -RepetitionDuration ($fin - $inicio)
    $ajustes = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 2) -Priority 7 -StartWhenAvailable
    Register-ScheduledTask -TaskName $nombreTarea -Action $accion -Trigger $disparo -Settings $ajustes `
        -Description 'Anota cada 5 min el consumo de la PC por familia de programas (registrar-consumo-pc.ps1).' -Force | Out-Null
    "Tarea '$nombreTarea' programada cada 5 min, hasta $($fin.ToString('dd/MM/yyyy HH:mm')). Datos en $carpeta"
    return
}

New-Item -ItemType Directory -Force $carpeta | Out-Null
$inv = [Globalization.CultureInfo]::InvariantCulture
$ahora = Get-Date

# Una sola consulta: nombre, línea de comando, padre, CPU acumulado y RAM de cada proceso.
# El pid 0 es el proceso INACTIVO: su "CPU" es tiempo ocioso y no se suma a nadie.
$procs = @(Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId, Name, CommandLine, CreationDate, KernelModeTime, UserModeTime, WorkingSetSize |
    Where-Object { $_.ProcessId -ne 0 })
$porPid = @{}
foreach ($p in $procs) { $porPid[[int]$p.ProcessId] = $p }

function Propia($p) {
    # Familia por la línea de comando del propio proceso; $null = decidir por quién lo lanzó.
    $n = "$($p.Name)".ToLower()
    $c = "$($p.CommandLine)"
    if ($n -eq 'msedge.exe') { return $null }
    if ($c -match 'skyia-vision') { return 'vision' }
    if ($c -match 'playwright|chequeo-pantallas|render_modulo|cmp_fotos') { return 'skyone_pantallas' }
    if ($c -match '\\skyone\\|/skyone/') { return 'skyone_otros' }
    if ($n -match '^claude' -or $c -match 'AnthropicClaude|claude-code|mcp-mail-empresa') { return 'claude' }
    if ($n -in 'msmpeng.exe', 'mpdefendercoreservice.exe', 'nissrv.exe') { return 'antivirus' }
    return $null
}

function Familia($p) {
    $actual = $p
    for ($i = 0; $i -lt 8 -and $actual; $i++) {
        $f = Propia $actual
        if ($f) { return $f }
        $actual = $porPid[[int]$actual.ParentProcessId]
    }
    if ("$($p.Name)".ToLower() -eq 'msedge.exe') { return 'edge_uso' }
    return 'windows_resto'
}

$familias = 'skyone_pantallas', 'skyone_otros', 'vision', 'claude', 'edge_uso', 'antivirus', 'windows_resto'
$cpu = @{}; $ram = @{}
foreach ($f in $familias) { $cpu[$f] = 0.0; $ram[$f] = 0.0 }

# Estado anterior: CPU acumulado por proceso (clave pid|creación, para no confundir un pid reusado).
$archivoEstado = Join-Path $carpeta 'estado.json'
$previo = @{}; $tPrevio = $null
if (Test-Path $archivoEstado) {
    try {
        $e = Get-Content $archivoEstado -Raw | ConvertFrom-Json
        $tPrevio = [datetime]::Parse($e.t, $inv)
        foreach ($prop in $e.cpu.PSObject.Properties) { $previo[$prop.Name] = [double]$prop.Value }
        $ociosoPrevio = [double]$e.ocioso; $relojPrevio = [double]$e.reloj
    } catch { $previo = @{}; $tPrevio = $null }
}
$intervalo = if ($tPrevio) { ($ahora - $tPrevio).TotalSeconds } else { 0 }
# Un hueco largo (PC apagada o suspendida) no se promedia: se anota la RAM y se reinicia la cuenta.
$valeCpu = $intervalo -ge 50 -and $intervalo -le 1200

# Ocupación TOTAL del intervalo (contador de tiempo ocioso de Windows). Incluye a los procesos que nacieron y
# murieron entre dos corridas —pruebas y comandos de los chats—, que por familia no se ven.
$crudo = Get-CimInstance Win32_PerfRawData_PerfOS_Processor -Filter "Name='_Total'" -Property PercentProcessorTime, Timestamp_Sys100NS
$ocioso = [double]$crudo.PercentProcessorTime; $reloj = [double]$crudo.Timestamp_Sys100NS
$cpuTotal = $null
if ($valeCpu -and $relojPrevio -and $reloj -gt $relojPrevio) {
    $cpuTotal = [math]::Max(0, 100 * (1 - ($ocioso - $ociosoPrevio) / ($reloj - $relojPrevio)))
}

$nuevo = @{}
foreach ($p in $procs) {
    $f = Familia $p
    $seg = ([double]$p.KernelModeTime + [double]$p.UserModeTime) / 1e7
    $clave = "$($p.ProcessId)|$($p.CreationDate.Ticks)"
    $nuevo[$clave] = $seg
    $ram[$f] += [double]$p.WorkingSetSize
    if ($valeCpu) {
        if ($previo.ContainsKey($clave)) { $d = $seg - $previo[$clave] }
        elseif ($p.CreationDate -gt $tPrevio) { $d = $seg }   # nació en el intervalo: todo su CPU es de acá
        else { $d = 0 }
        if ($d -gt 0) { $cpu[$f] += $d }
    }
}
@{ t = $ahora.ToString('o', $inv); cpu = $nuevo; ocioso = $ocioso; reloj = $reloj } | ConvertTo-Json -Compress | Set-Content $archivoEstado -Encoding UTF8

$nucleos = [Environment]::ProcessorCount
$so = Get-CimInstance Win32_OperatingSystem -Property TotalVisibleMemorySize, FreePhysicalMemory, TotalVirtualMemorySize, FreeVirtualMemory
$proc = Get-CimInstance Win32_PerfFormattedData_Counters_ProcessorInformation -Filter "Name='_Total'" -Property PercentProcessorUtility, PercentProcessorPerformance

function N($x, $dec) { if ($null -eq $x) { '' } else { [math]::Round([double]$x, $dec).ToString($inv) } }

$fila = [ordered]@{
    fecha              = $ahora.ToString('yyyy-MM-dd HH:mm:ss')
    intervalo_s        = N $intervalo 0
    cpu_trabajo_real   = N $proc.PercentProcessorUtility 0
    cpu_velocidad_pct  = N $proc.PercentProcessorPerformance 0
    ram_usada_gb       = N (($so.TotalVisibleMemorySize - $so.FreePhysicalMemory) / 1MB) 2
    ram_total_gb       = N ($so.TotalVisibleMemorySize / 1MB) 2
    comprometida_gb    = N (($so.TotalVirtualMemorySize - $so.FreeVirtualMemory) / 1MB) 2
    comprometida_tope_gb = N ($so.TotalVirtualMemorySize / 1MB) 2
}
foreach ($f in $familias) {
    $fila["cpu_$f"] = if ($valeCpu) { N ($cpu[$f] * 100 / ($intervalo * $nucleos)) 1 } else { '' }
    $fila["ram_$f"] = N ($ram[$f] / 1GB) 2
}
$fila['costo_registro_s'] = N ([Diagnostics.Process]::GetCurrentProcess().TotalProcessorTime.TotalSeconds) 2
# Misma vara que las familias (tiempo de procesador, no «trabajo real»): la diferencia es lo que no se atribuye.
$fila['cpu_total_intervalo'] = N $cpuTotal 1
$sumaFamilias = 0.0; foreach ($f in $familias) { $sumaFamilias += $cpu[$f] * 100 / [math]::Max(1, $intervalo * $nucleos) }
$fila['cpu_no_atribuido'] = if ($null -ne $cpuTotal) { N ([math]::Max(0, $cpuTotal - $sumaFamilias)) 1 } else { '' }

$csv = Join-Path $carpeta ("consumo-{0}.csv" -f $ahora.ToString('yyyy-MM-dd'))
$encabezado = $fila.Keys -join ','
if ((Test-Path $csv) -and (Get-Content $csv -TotalCount 1) -ne $encabezado) {
    # Cambiaron las columnas: lo anterior del día queda aparte, intacto, en vez de mezclar formatos.
    Rename-Item $csv ("consumo-{0}-antes-{1}.csv" -f $ahora.ToString('yyyy-MM-dd'), $ahora.ToString('HHmm'))
}
if (-not (Test-Path $csv)) { $encabezado | Set-Content $csv -Encoding UTF8 }
($fila.Values -join ',') | Add-Content $csv -Encoding UTF8
