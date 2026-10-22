' Lanzador SIN ventana de registrar-consumo-pc.ps1 para la tarea programada (ver ese archivo).
' powershell.exe solo abre una ventana aunque se le pida oculta; la sesión S4U pide administrador.
Set fso = CreateObject("Scripting.FileSystemObject")
ps1 = fso.BuildPath(fso.GetParentFolderName(WScript.ScriptFullName), "registrar-consumo-pc.ps1")
CreateObject("WScript.Shell").Run "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File """ & ps1 & """", 0, True
