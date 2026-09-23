# Verifica que el symlink global ~/.claude/CLAUDE.md este sano, y ademas que el archivo que ese
# CLAUDE.md manda leer (entorno-windows.md) exista Y este en la ruta que el CLAUDE.md CITA.
# Lo del symlink:
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
# -Quiet : modo hook. No imprime el mensaje de exito y SIEMPRE sale con 0: Claude Code solo
#          le pasa a la sesion lo que imprime un hook que sale con 0, asi que salir con 1
#          escondia justamente los avisos.
#
# Ademas controla que ~/.claude/skills este atado a la carpeta skills del repo, y que el
# repo no tenga cambios sin commitear (la otra computadora no los ve).

param([switch]$Quiet)

# Enlazado hay UNO SOLO (el CLAUDE.md, que el harness carga desde ~/.claude). El otro archivo
# del repo -- entorno-windows.md -- se verifica distinto, mas abajo: no es un symlink, el
# CLAUDE.md lo cita por su ruta en el repo. Igual se chequea que EXISTA, porque un puntero a
# la nada deja las trampas de la maquina sin aviso.
$archivos = @('CLAUDE.md')
$fallas   = 0

function Aviso($nombre, $msg) { Write-Host "[$nombre] $msg" -ForegroundColor Yellow }

foreach ($nombre in $archivos) {
    $globalFile = Join-Path $env:USERPROFILE (Join-Path '.claude' $nombre)
    $repoFile   = Join-Path $PSScriptRoot $nombre

    # 1. Existe algo en el global?
    if (-not (Test-Path $globalFile)) {
        Aviso $nombre "No existe ~/.claude/$nombre -> NO se esta cargando (ni se puede leer cuando se pide)."
        Aviso $nombre "Arreglalo con:  .\setup-symlink.ps1"
        $fallas++
        continue
    }

    $item = Get-Item $globalFile -Force

    # 2. Es un symlink?
    if ($item.LinkType -ne 'SymbolicLink') {
        $kind = if ($item.LinkType) { $item.LinkType } else { 'archivo real' }
        Aviso $nombre "~/.claude/$nombre existe pero NO es un symlink (es: $kind)."
        Aviso $nombre "Puede desincronizarse del repo. Recrealo con:  .\setup-symlink.ps1"
        $fallas++
        continue
    }

    # 3. El destino al que apunta sigue existiendo?
    $target = @($item.Target)[0]
    if (-not (Test-Path $target)) {
        Aviso $nombre "El symlink esta ROTO: apunta a '$target' que ya no existe."
        Aviso $nombre "(Tipico si renombraste o moviste la carpeta del repo.)"
        Aviso $nombre "Arreglalo con:  .\setup-symlink.ps1"
        $fallas++
        continue
    }

    # 4. Apunta al archivo de este mismo repo?
    if (-not (Test-Path $repoFile)) {
        Aviso $nombre "El symlink resuelve, pero en ESTE repo no hay un $nombre contra que compararlo."
        $fallas++
        continue
    }
    if ((Resolve-Path $target).Path -ne (Resolve-Path $repoFile).Path) {
        Aviso $nombre "El symlink resuelve, pero apunta a OTRO $nombre :"
        Aviso $nombre "  apunta a:  $target"
        Aviso $nombre "  este repo: $repoFile"
        Aviso $nombre "Si queres que apunte aca, corre:  .\setup-symlink.ps1"
        $fallas++
        continue
    }

    if (-not $Quiet) {
        Write-Host "[$nombre] OK -> symlink sano apuntando a $target" -ForegroundColor Green
    }
}

# El archivo que el CLAUDE.md manda leer antes de tocar la consola. No es un symlink, asi que
# lo que hay que verificar es OTRA cosa: que exista, y sobre todo que este donde el CLAUDE.md
# DICE que esta. Esa ruta esta escrita a mano adentro del CLAUDE.md y el repo se puede clonar
# en cualquier lado (el README lo dice), asi que es lo unico del esquema que se puede romper
# sin que nadie se entere: un puntero que no resuelve no da error, simplemente no se lee.
$entorno = Join-Path $PSScriptRoot 'entorno-windows.md'
if (-not (Test-Path $entorno)) {
    Aviso 'entorno-windows.md' "Falta en el repo ($entorno). El CLAUDE.md lo cita y no lo va a encontrar."
    $fallas++
} else {
    # Sacar del CLAUDE.md las rutas que cita para este archivo y ver si alguna NO resuelve.
    $claudeMd = Join-Path $PSScriptRoot 'CLAUDE.md'
    $citasMalas = @()
    if (Test-Path $claudeMd) {
        foreach ($linea in (Get-Content -LiteralPath $claudeMd -Encoding UTF8)) {
            foreach ($m in [regex]::Matches($linea, '[A-Za-z]:\\[^\s`)]*entorno-windows\.md|~/\.claude/entorno-windows\.md')) {
                $ruta = $m.Value
                # El ~/.claude/ no existe a proposito: ese archivo NO se enlaza (hace falta admin).
                if ($ruta -like '~*') { $citasMalas += $ruta; continue }
                if (-not (Test-Path $ruta)) { $citasMalas += $ruta }
            }
        }
    }
    if ($citasMalas.Count -gt 0) {
        Aviso 'entorno-windows.md' ("El CLAUDE.md lo cita por una ruta que NO resuelve en esta maquina: " +
            (($citasMalas | Select-Object -Unique) -join ', ') + ". Existe en: $entorno")
        Aviso 'entorno-windows.md' "Corregi la ruta adentro del CLAUDE.md (o clona el repo en la ruta que cita)."
        $fallas++
    } elseif (-not $Quiet) {
        Write-Host "[entorno-windows.md] OK -> presente en $entorno y el CLAUDE.md lo cita bien" -ForegroundColor Green
    }
}

# Skills globales: ~/.claude/skills tiene que ser un link a la carpeta skills de este repo.
$repoSkills   = Join-Path $PSScriptRoot 'skills'
$globalSkills = Join-Path $env:USERPROFILE (Join-Path '.claude' 'skills')
if (Test-Path $repoSkills) {
    $skillsOk = $false
    if (Test-Path $globalSkills) {
        $gs = Get-Item $globalSkills -Force
        if ($gs.LinkType -in @('Junction', 'SymbolicLink')) {
            $gt = @($gs.Target)[0]
            if ($gt -and (Test-Path $gt) -and ((Resolve-Path $gt).Path -eq (Resolve-Path $repoSkills).Path)) { $skillsOk = $true }
        }
    }
    if (-not $skillsOk) {
        Aviso 'skills' "~/.claude/skills no esta atado a la carpeta skills del repo: las skills no viajan entre computadoras. Arreglalo con:  .\setup-symlink.ps1"
        $fallas++
    }
}

# Cambios sin commitear en este repo: la otra computadora trabaja con reglas viejas sin enterarse.
if (Get-Command git -ErrorAction SilentlyContinue) {
    $pendientes = @(& git -C $PSScriptRoot status --porcelain 2>$null)
    if ($pendientes.Count -gt 0) {
        Aviso 'repo' "Mi-config-de-Claude tiene $($pendientes.Count) cambio(s) sin commitear: la otra computadora no los ve. Commitealos y subilos (no hace falta preguntar)."
        $fallas++
    }
}

if ($Quiet) { exit 0 }
if ($fallas -gt 0) { exit 1 }
exit 0
