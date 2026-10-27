#!/bin/sh
# Prueba de mutacion del pre-commit: le mete las violaciones en un repo descartable y
# verifica que TODAVIA las caza, y que un estado limpio pasa. Si esto falla, el control puede
# estar en verde sin revisar nada. Uso: sh .githooks/probar-pre-commit.sh

HOOK="$(cd "$(dirname "$0")" && pwd)/pre-commit"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cd "$TMP" && git init -q . && mkdir kit-proyecto-nuevo
mal=0

caso() { # $1 = esperado (0 pasa / 1 frena), $2 = descripcion
    git add -A >/dev/null 2>&1
    sh "$HOOK" >/dev/null 2>&1; r=$?
    if [ "$r" -eq "$1" ]; then echo "ok   $2"; else echo "MAL  $2 (salio $r, esperaba $1)"; mal=1; fi
}

echo "chico" > CLAUDE.md; echo "texto neutro sobre federalismo" > kit-proyecto-nuevo/a.md
caso 0 "estado limpio pasa (y 'federalismo' no se confunde con un nombre)"

echo "lo armamos en SkyOne" > kit-proyecto-nuevo/a.md
caso 1 "un nombre de producto en el kit frena"

echo "texto neutro" > kit-proyecto-nuevo/a.md
head -c 23000 /dev/zero | tr '\0' 'x' > CLAUDE.md
caso 1 "CLAUDE.md por encima del tope frena"

echo "chico" > CLAUDE.md
echo "import sys; sys.exit(1)" > kit-proyecto-nuevo/test_chequear_gatillos.py
caso 1 "el test del chequeo de gatillos en rojo frena"

echo "import sys; sys.exit(0)" > kit-proyecto-nuevo/test_chequear_gatillos.py
caso 0 "el test del chequeo de gatillos en verde pasa"

exit $mal
