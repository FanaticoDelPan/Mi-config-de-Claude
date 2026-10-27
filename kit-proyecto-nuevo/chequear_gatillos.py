"""Avisa qué gatillos de docs/escalar-el-arnes.md ya se cumplieron y nadie decidió qué hacer.

Los gatillos escritos en prosa dependen de que alguien los relea, y no los relee nadie: la foto anterior del
kit quedó vieja en seis semanas sin que nada avisara. Este chequeo mide los que se pueden contar mirando el
repo y nombra los cumplidos que no tienen decisión declarada en docs/gatillos.json.

Es un AVISO (patrones-de-control.md §Duro vs. aviso): un gatillo cumplido no frena nada. Lo único que frena
(salida 1) es lo objetivamente falso: una declaración mal escrita, o una que nombra un gatillo que ya no existe.

    python -I scripts/chequear_gatillos.py              # en el pre-commit: si el chequeo se rompe, avisa y deja pasar
    python -I scripts/chequear_gatillos.py --estricto   # en la CI: si se rompe o el documento cambió, falla

docs/gatillos.json, un valor por gatillo cumplido:
    {"Prosa repetida": "adoptada", "Guarda de rama": "#12", "Piso de rollback": "no: la base es de solo lectura",
     "Validador de enlaces internos": "pendiente: docs/pendientes.md"}
«pendiente: <archivo>» es para el proyecto que lleva lo pendiente en un archivo y no en tickets: vale mientras
ese archivo nombre el gatillo tal cual.
"""

import argparse
import functools
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DOC = Path("docs") / "escalar-el-arnes.md"
DECLARACION = Path("docs") / "gatillos.json"
VALOR_VALIDO = re.compile(r"^(adoptada|#\d+|no: .{10,}|pendiente: \S+)$")
SALTEAR = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".worktrees", ".mypy_cache",
           ".next", "worktrees"}
CODIGO = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cs", ".go", ".rs", ".java", ".rb", ".php", ".sql",
          ".sh", ".ps1", ".kt", ".swift", ".vue", ".svelte"}
FECHA_EN_COMENTARIO = re.compile(r"(#|//|/\*|^\s*\*|--)\s.*\b20\d\d-[01]\d-[0-3]\d\b")
CARPETA_MIGRACIONES = {"migrations", "migraciones", "versions", "migrate"}
DESTRUCTIVO = re.compile(r"drop_table|drop_column|\bDROP\s+(TABLE|COLUMN)\b", re.IGNORECASE)
CREDENCIAL_EXTERNA = re.compile(r"^([A-Z0-9_]+?)_(URL|HOST|TOKEN|API_KEY|KEY|DSN|SECRET)\s*=", re.MULTILINE)
# Una variable cuyo nombre lleva una de estas palabras es infraestructura del propio proyecto, no un sistema de otro.
INFRA_PROPIA = {"DATABASE", "DB", "POSTGRES", "PG", "MYSQL", "REDIS", "SUPABASE", "FIREBASE", "SECRET", "SESSION",
                "APP", "AUTH", "NEXTAUTH", "JWT", "CSRF", "SITE", "BASE"}


@functools.lru_cache(maxsize=None)
def _todos(raiz):
    """Los archivos del proyecto: los que git no ignora (así no entran la salida de un build ni lo generado), o,
    fuera de un repo, un recorrido que poda lo conocido."""
    r = subprocess.run(["git", "-C", str(raiz), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                       capture_output=True, text=True, encoding="utf-8", env=git_sin_herencia())
    if r.returncode == 0:
        return tuple(raiz / p for p in r.stdout.split("\0") if p and not SALTEAR.intersection(Path(p).parts))
    rutas = []
    # os.walk podando, no rglob filtrando: rglob recorre node_modules entero antes de descartarlo (5 s contra 0,7).
    for carpeta, subcarpetas, nombres in os.walk(raiz):
        subcarpetas[:] = [s for s in subcarpetas if s not in SALTEAR]
        rutas.extend(Path(carpeta) / n for n in nombres)
    return tuple(rutas)


def _archivos(raiz, sufijos):
    for ruta in _todos(raiz):
        if ruta.suffix.lower() in sufijos and ruta.is_file():
            yield ruta


def _leer(ruta):
    try:
        return ruta.read_text(encoding="utf-8", errors="replace") if ruta.stat().st_size < 1_000_000 else ""
    except OSError:
        return ""


def _docs(raiz):
    carpeta = raiz / "docs"
    return list(_archivos(carpeta, {".md"})) if carpeta.is_dir() else []


def git_sin_herencia():
    """El entorno sin las variables GIT_*: adentro de un hook, git las fija y un `git -C <otra carpeta>`
    terminaría operando sobre el repo que está commiteando, no sobre la carpeta pedida."""
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _etiquetas(raiz):
    r = subprocess.run(["git", "-C", str(raiz), "tag", "--list"], capture_output=True, text=True,
                       env=git_sin_herencia())
    return [t for t in r.stdout.split() if t] if r.returncode == 0 else []


def _paquete_publicable(ruta):
    try:
        datos = json.loads(_leer(ruta) or "{}")
    except json.JSONDecodeError:
        return False
    return "publishConfig" in datos or ("bin" in datos and not datos.get("private"))


def _algo_publicado(raiz):
    etiquetas = _etiquetas(raiz)
    if etiquetas:
        return f"hay {len(etiquetas)} etiqueta(s) de versión"
    flujos = raiz / ".github" / "workflows"
    if flujos.is_dir():
        for f in flujos.iterdir():
            if re.search(r"publi|release|deploy|despleg", f.name, re.IGNORECASE):
                return f"hay un workflow de publicar ({f.name})"
    # Se publica desde la máquina, sin etiquetas ni workflow: un proyecto atado a una plataforma, o un paquete.
    for marca in (".vercel/project.json", "vercel.json", "netlify.toml", "fly.toml", "render.yaml", "Procfile"):
        if (raiz / marca).is_file():
            return f"está atado a una plataforma de publicación ({marca})"
    for ruta in [raiz / "package.json", *raiz.glob("*/package.json")]:
        if ruta.is_file() and _paquete_publicable(ruta):
            return f"hay un paquete que se publica ({ruta.relative_to(raiz).as_posix()})"
    return None


def _cantidad_docs(minimo):
    def medir(raiz):
        n = len(_docs(raiz))
        return f"hay {n} documentos en docs/ (gatillo: {minimo})" if n >= minimo else None
    return medir


def _reglas_de_area(raiz):
    guias = sorted(p.name for p in (raiz / "docs").glob("reglas-*.md")) if (raiz / "docs").is_dir() else []
    return f"existe {guias[0]}" if guias else None


def _fechas_en_codigo(raiz):
    for ruta in _archivos(raiz, CODIGO):
        for n, linea in enumerate(_leer(ruta).splitlines(), 1):
            if FECHA_EN_COMENTARIO.search(linea):
                return f"fecha en un comentario: {ruta.relative_to(raiz).as_posix()}:{n}"
    return None


def _skill_propio(raiz):
    skills = sorted((raiz / ".claude" / "skills").glob("*/SKILL.md"))
    return f"existe el skill {skills[0].parent.name}" if skills else None


def _migracion_destructiva(raiz):
    for ruta in _archivos(raiz, {".py", ".sql", ".js", ".ts", ".rb"}):
        if CARPETA_MIGRACIONES.intersection(ruta.relative_to(raiz).parts) and DESTRUCTIVO.search(_leer(ruta)):
            return f"migración destructiva: {ruta.relative_to(raiz).as_posix()}"
    return None


def _publicaciones_revisadas(raiz):
    n = len(_etiquetas(raiz))
    return f"hay {n} etiquetas de versión (gatillo: ~5 publicaciones)" if n >= 5 else None


def _credenciales_de_terceros(raiz):
    for nombre in (".env.example", ".env.sample", ".env.template"):
        ruta = raiz / nombre
        if ruta.is_file():
            ajenas = [m.group(0).split("=")[0].strip() for m in CREDENCIAL_EXTERNA.finditer(_leer(ruta))
                      if not INFRA_PROPIA.intersection(m.group(1).split("_"))]
            if ajenas:
                return f"{nombre} declara credenciales de un servicio externo ({ajenas[0]})"
    return None


# El nombre es la fila de escalar-el-arnes.md tal cual (su primer tramo en negrita): es la llave de la
# declaración y lo que el test de consistencia busca en el documento. La señal es una aproximación del
# gatillo; cuando se equivoca, se declara «no: <motivo>» y no vuelve a avisar.
GATILLOS = {
    "Reglas que llegan solas": _reglas_de_area,
    "Guarda de rama": _algo_publicado,
    "Sin fechas ni autores en el código y los docs": _fechas_en_codigo,
    "Prosa repetida": _cantidad_docs(10),
    "Validador de enlaces internos": _cantidad_docs(2),
    "Tope del cuerpo de cada skill": _skill_propio,
    "Alarma del total de la doc": _cantidad_docs(30),
    "Revisor adversarial antes de publicar": _algo_publicado,
    "Registro de hallazgos por ángulo y de escapes a producción": _publicaciones_revisadas,
    "Piso de rollback": _migracion_destructiva,
    "Ley de dónde vive cada hecho, extendida": _cantidad_docs(11),
    "Método para conectar sistemas de otros": _credenciales_de_terceros,
}


def filas_del_documento(texto):
    """Los nombres de los gatillos: el primer tramo en negrita de cada fila de tabla."""
    return [m.group(1) for m in re.finditer(r"^\|\s*\*\*(.+?)\*\*", texto, re.MULTILINE)]


def chequear(raiz):
    """Devuelve (avisos, desajustes, errores, resumen).

    Errores: la declaración está mal (frena siempre). Desajustes: el documento ya no dice lo que este chequeo
    mide (frena solo con --estricto: en el día a día no puede trabar un commit que no tiene nada que ver)."""
    avisos, desajustes, errores = [], [], []
    doc = raiz / DOC
    filas = filas_del_documento(_leer(doc)) if doc.is_file() else None
    if filas is None:
        desajustes.append(f"no encuentro {DOC.as_posix()}: el chequeo no sabe qué gatillos rigen")
    else:
        for nombre in GATILLOS:
            if nombre not in filas:
                desajustes.append(f"«{nombre}» ya no es una fila de {DOC.as_posix()}: actualizar este chequeo")

    declarado = {}
    ruta_decl = raiz / DECLARACION
    if ruta_decl.is_file():
        try:
            declarado = json.loads(_leer(ruta_decl) or "{}")
        except json.JSONDecodeError as e:
            errores.append(f"{DECLARACION.as_posix()} no es JSON válido: {e}")
        for nombre, valor in declarado.items():
            if nombre not in GATILLOS:
                errores.append(f"{DECLARACION.as_posix()} declara «{nombre}», que no es un gatillo medido: borrarlo")
            elif not isinstance(valor, str) or not VALOR_VALIDO.match(valor):
                errores.append(f"«{nombre}»: el valor tiene que ser \"adoptada\", \"#N\", \"no: <motivo>\" "
                               "o \"pendiente: <archivo>\"")
            elif valor.startswith("pendiente: "):
                # Un proyecto sin tickets lleva lo pendiente en un archivo: ese archivo tiene que nombrar el
                # gatillo, o la declaración apunta a la nada (alguien lo borró de la lista sin resolverlo).
                lista = raiz / valor.split(": ", 1)[1]
                if nombre not in _leer(lista):
                    errores.append(f"«{nombre}» se declaró pendiente en {lista.relative_to(raiz).as_posix()}, "
                                   "y ese archivo no lo nombra: o volvió a la lista, o se resolvió y se declara")

    for nombre, medir in GATILLOS.items():
        if nombre not in declarado:
            senal = medir(raiz)
            if senal:
                avisos.append(f"{nombre}: {senal}")

    total = f" de {len(filas)}" if filas else ""
    resumen = f"Gatillos: {len(GATILLOS)}{total} se miden solos; {len(avisos)} cumplido(s) sin decisión."
    return avisos, desajustes, errores, resumen


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):  # la consola de Windows no es UTF-8 por defecto
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--raiz", type=Path, default=Path.cwd())
    p.add_argument("--estricto", action="store_true", help="falla si el chequeo se rompe (para la CI)")
    args = p.parse_args(argv)
    try:
        avisos, desajustes, errores, resumen = chequear(args.raiz.resolve())
    except Exception as e:  # fail-open en el día a día: un aviso roto no puede frenar el trabajo
        print(f"chequeo de gatillos roto: {e!r}")
        return 1 if args.estricto else 0
    print(resumen)
    for a in avisos:
        print(f"  - {a}")
    if avisos:
        print(f"  Decidir cada uno en {DECLARACION.as_posix()}: adoptada, su ticket, o «no» con motivo.")
    for d in desajustes:
        print(f"{'ERROR' if args.estricto else 'AVISO'}: {d}")
    for e in errores:
        print(f"ERROR: {e}")
    return 1 if errores or (args.estricto and desajustes) else 0


if __name__ == "__main__":
    sys.exit(main())
