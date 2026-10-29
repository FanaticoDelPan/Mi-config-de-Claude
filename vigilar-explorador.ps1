<#
Vigila los recursos de dibujo (GDI) del Explorador para encontrar QUÉ se los come.

Por qué: el Explorador se cierra a propósito cuando pasa de GDIProcessHandleQuota - 500 objetos GDI
(9.500 con el tope por omisión de 10.000; está en CTray::CheckGDIHandleLimit, el desplazamiento 0x6698e de
las caídas). Algo que se hace con la PC le deja objetos sin liberar; los intervalos entre caídas (40 min
a 20 h) dicen que va a ráfagas. Esta vigía anota cada 30 s cuántos tiene, de qué tipo, qué programa está
al frente y qué carpetas hay abiertas: el minuto en que la cuenta trepa señala al culpable.

Corre en la sesión del usuario (la tarea del registro de consumo corre en otra sesión y no ve la ventana
del frente ni las carpetas abiertas). Un solo proceso que duerme entre muestras: compila una vez.

Uso:
  vigilar-explorador.ps1                -> vigila hasta que se cierra la sesión (lo que lanza la tarea)
  vigilar-explorador.ps1 -Instalar      -> la arranca ahora y en cada inicio de sesión, sin ventana
  vigilar-explorador.ps1 -Desinstalar   -> borra la tarea (los CSV quedan)
  vigilar-explorador.ps1 -Una           -> una sola muestra (para probarla)
Datos: %USERPROFILE%\registro-consumo-pc\explorador-AAAA-MM-DD.csv
#>
param([switch]$Instalar, [switch]$Desinstalar, [switch]$Una, [ValidateRange(5, 600)][int]$Segundos = 30)

$ErrorActionPreference = 'Stop'
$nombreTarea = 'vigilar-explorador'
# NO en AppData: lo que escribe un comando lanzado desde la app de Claude (paquete MSIX) va a una copia privada.
$carpeta = Join-Path $env:USERPROFILE 'registro-consumo-pc'
New-Item -ItemType Directory -Force $carpeta | Out-Null
trap {
    Add-Content (Join-Path $carpeta 'errores.log') ("{0} vigilar-explorador {1} | {2}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $_, $_.InvocationInfo.PositionMessage)
    exit 1
}

if ($Desinstalar) {
    Unregister-ScheduledTask -TaskName $nombreTarea -Confirm:$false
    Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object CommandLine -match 'vigilar-explorador' |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
    "Tarea borrada. Los datos quedan en $carpeta"
    return
}

if ($Instalar) {
    $wscript = Join-Path $env:SystemRoot 'System32\wscript.exe'
    $vbs = [IO.Path]::ChangeExtension($PSCommandPath, '.vbs')
    $accion = New-ScheduledTaskAction -Execute $wscript -Argument "//B //Nologo `"$vbs`""
    $disparo = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    $ajustes = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -Priority 7
    $quien = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
    Register-ScheduledTask -TaskName $nombreTarea -Action $accion -Trigger $disparo -Settings $ajustes -Principal $quien `
        -Description 'Anota cada 30 s los recursos GDI del Explorador (vigilar-explorador.ps1).' -Force | Out-Null
    Start-ScheduledTask -TaskName $nombreTarea
    "Tarea '$nombreTarea' instalada y corriendo. Datos en $carpeta"
    return
}

$src = @'
using System; using System.Text; using System.Runtime.InteropServices; using System.Collections.Generic;
public static class VigiaGdi {
  [DllImport("ntdll.dll")] static extern int NtQueryInformationProcess(IntPtr h, int c, ref PBI p, int l, out int r);
  [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(int a, bool i, int pid);
  [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
  [DllImport("kernel32.dll")] static extern bool ReadProcessMemory(IntPtr h, IntPtr b, byte[] buf, IntPtr n, out IntPtr r);
  [DllImport("user32.dll")] public static extern uint GetGuiResources(IntPtr h, uint f);
  [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr w, out uint pid);
  [StructLayout(LayoutKind.Sequential)] struct PBI { public IntPtr R1; public IntPtr Peb; public IntPtr R2a; public IntPtr R2b; public IntPtr Pid; public IntPtr R3; }
  public static uint PidAlFrente() { uint p; GetWindowThreadProcessId(GetForegroundWindow(), out p); return p; }
  // Objetos GDI del proceso por tipo (1 DC, 4 region, 5 bitmap, 10 fuente, 16 pincel), de la tabla compartida de GDI.
  public static int[] Contar(int pid) {
    int[] t = new int[128];
    IntPtr h = OpenProcess(0x0410, false, pid);
    if (h == IntPtr.Zero) return t;
    try {
      PBI p = new PBI(); int r; IntPtr n;
      NtQueryInformationProcess(h, 0, ref p, Marshal.SizeOf(p), out r);
      byte[] ptr = new byte[8];
      if (!ReadProcessMemory(h, p.Peb + 0xF8, ptr, (IntPtr)8, out n)) return t;
      byte[] buf = new byte[0x10000 * 24];
      if (!ReadProcessMemory(h, (IntPtr)BitConverter.ToInt64(ptr, 0), buf, (IntPtr)buf.Length, out n)) return t;
      for (int i = 0; i < 0x10000; i++) {
        int o = i * 24;
        if (BitConverter.ToUInt16(buf, o + 8) == (pid & 0xffff)) t[buf[o + 14] & 0x7f]++;
      }
    } finally { CloseHandle(h); }
    return t;
  }
}
'@
Add-Type -TypeDefinition $src
$shell = New-Object -ComObject Shell.Application

while ($true) {
    $ahora = Get-Date
    $exp = Get-Process explorer -ErrorAction SilentlyContinue | Sort-Object StartTime | Select-Object -First 1
    # Si el Explorador se cae entre que se lo busca y se lo mide, su Handle viene vacío: se saltea la muestra
    # en vez de morir (el trap cortaba la vigía justo en la caída que tenía que registrar).
    if ($exp -and $exp.Handle) {
        $t = [VigiaGdi]::Contar($exp.Id)
        $frente = ''
        try { $frente = (Get-Process -Id ([VigiaGdi]::PidAlFrente()) -ErrorAction Stop).ProcessName } catch {}
        $carpetas = @()
        try { $carpetas = @($shell.Windows() | ForEach-Object { $_.LocationURL }) } catch {}
        $fila = [ordered]@{
            fecha = $ahora.ToString('yyyy-MM-dd HH:mm:ss')
            explorer_pid = $exp.Id
            explorer_desde = $exp.StartTime.ToString('yyyy-MM-dd HH:mm:ss')
            gdi = [VigiaGdi]::GetGuiResources($exp.Handle, 0)
            user = [VigiaGdi]::GetGuiResources($exp.Handle, 1)
            bitmap = $t[5]; dc = $t[1]; region = $t[4]; fuente = $t[10]; pincel = $t[16]
            al_frente = $frente
            carpetas_abiertas = $carpetas.Count
            # La ruta va sin comas para no romper el CSV.
            carpetas = (($carpetas | ForEach-Object { [uri]::UnescapeDataString("$_") -replace ',', ' ' }) -join ' | ')
        }
        $csv = Join-Path $carpeta ("explorador-{0}.csv" -f $ahora.ToString('yyyy-MM-dd'))
        if (-not (Test-Path $csv)) { ($fila.Keys -join ',') | Set-Content $csv -Encoding UTF8 }
        ($fila.Values -join ',') | Add-Content $csv -Encoding UTF8
        if ($Una) { $fila; return }
    }
    Start-Sleep -Seconds $Segundos
}
