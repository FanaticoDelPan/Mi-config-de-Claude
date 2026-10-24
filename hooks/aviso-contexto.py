"""Aviso de contexto y de costo del chat (hook de Claude Code: UserPromptSubmit y PostToolUse).

Regla 3 del CLAUDE.md. Cada umbral avisa UNA vez por chat, pegado al trabajo en curso, para que Claude
no gaste un turno en preguntar "¿seguimos?":
  contexto 40 % -> una línea al pie nombrando el corte natural; desde ahí, el estado escrito al avanzar
  contexto 60 % -> checkpoint armado al pie (qué quedó terminado, qué falta) y se sigue si no hay respuesta
  contexto 75 % -> Claude cierra el trabajo, con el traspaso escrito
  costo 2 y 4 puntos de cuota (chat + subagentes) -> cazan el chat que gasta sin agrandarse

El precio y los USD por punto salen de medir-consumo-semanal.py (al lado de esta carpeta): se
recalibran ahí y este aviso los toma solo. Si el contexto baja (compactación), los avisos de contexto
se rearman.

Lee la entrada del hook por stdin; si no hay nada que avisar no imprime nada. Nunca falla hacia
afuera: un error se traga y sale con 0, porque un aviso roto no puede trabar el chat.

Prueba a mano:  python -I aviso-contexto.py --probar <ruta del .jsonl de un chat>
"""
import glob
import importlib.util
import json
import os
import sys
import time

sys.dont_write_bytecode = True  # cargar el medidor dejaba __pycache__ adentro del repo
AQUI = os.path.dirname(os.path.abspath(__file__))
ESTADO_DIR = os.path.join(os.path.expanduser("~"), ".claude", "aviso-contexto")  # fuera de AppData (MSIX)
UMBRALES_CTX = (0.40, 0.60, 0.75)
UMBRALES_PTS = (2, 4)


def medidor():
    """precio() y USD_POR_PUNTO del medidor semanal, para que haya una sola calibración."""
    ruta = os.path.join(os.path.dirname(AQUI), "medir-consumo-semanal.py")
    spec = importlib.util.spec_from_file_location("medidor", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.precio, mod.USD_POR_PUNTO


def ventana(modelo):
    forzada = os.environ.get("AVISO_CONTEXTO_VENTANA")
    if forzada:
        return int(forzada)
    if os.environ.get("CLAUDE_CODE_DISABLE_1M_CONTEXT") == "1" or "haiku" in (modelo or ""):
        return 200_000
    return 1_000_000  # Opus 5.5, Opus 5, Fable y Sonnet 5 corren con 1M en Claude Code


def usd_de(u, modelo, precio):
    p = precio(modelo)
    a, b, r, o = (u.get(k) or 0 for k in
                  ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))
    b1h = min((u.get("cache_creation") or {}).get("ephemeral_1h_input_tokens") or 0, b)
    return (a * p[0] + (b - b1h) * p[0] * 1.25 + b1h * p[0] * 2 + r * p[1] + o * p[2]) / 1e6


def leer_nuevo(ruta, st, precio):
    """Suma lo que se agregó al archivo desde la última vez. Devuelve el último uso del chat principal.
    Un mismo mensaje se escribe en varias líneas con la salida a medio contar: vale la más alta."""
    f = st["archivos"].setdefault(ruta, {"pos": 0, "ids": {}})
    ultimo = None
    try:
        tam = os.path.getsize(ruta)
    except OSError:
        return None
    if tam < f["pos"]:  # el archivo se reescribió: se cuenta de nuevo
        f["pos"], f["ids"] = 0, {}
    with open(ruta, "rb") as h:
        h.seek(f["pos"])
        datos = h.read()
    corte = datos.rfind(b"\n") + 1  # solo líneas completas; la mitad que falta entra la próxima vez
    f["pos"] += corte
    for linea in datos[:corte].decode("utf-8", "ignore").splitlines():
        if '"usage"' not in linea:
            continue
        try:
            d = json.loads(linea)
        except ValueError:
            continue
        m = d.get("message") or {}
        u = m.get("usage")
        if d.get("type") != "assistant" or not u:
            continue
        clave = m.get("id") or d.get("uuid")
        f["ids"][clave] = max(f["ids"].get(clave, 0.0), usd_de(u, m.get("model"), precio))
        if not d.get("isSidechain"):
            ultimo = (u, m.get("model"))
    return ultimo


def fmt(n, dec=1):
    return f"{n:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def avisos(entrada):
    if entrada.get("agent_id"):  # adentro de un subagente no se avisa: el aviso es del chat
        return None
    trans = entrada.get("transcript_path")
    sesion = entrada.get("session_id")
    if not trans or not sesion or not os.path.exists(trans):
        return None
    precio, usd_por_punto = medidor()

    os.makedirs(ESTADO_DIR, exist_ok=True)
    ruta_st = os.path.join(ESTADO_DIR, f"{sesion}.json")
    try:
        with open(ruta_st, encoding="utf-8") as h:
            st = json.load(h)
    except (OSError, ValueError):
        st = {"archivos": {}, "ctx_nivel": 0, "pts_nivel": 0, "ctx": None}

    ultimo = leer_nuevo(trans, st, precio)
    for sub in glob.glob(os.path.join(trans[:-6], "subagents", "*.jsonl")):
        leer_nuevo(sub, st, precio)
    if ultimo:
        u, modelo = ultimo
        st["ctx"] = [sum(u.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens",
                                                   "cache_read_input_tokens", "output_tokens")), modelo]
    usd = sum(v for f in st["archivos"].values() for v in f["ids"].values())
    pts = usd / usd_por_punto

    msgs = []
    if st["ctx"]:
        tokens, modelo = st["ctx"]
        cap = ventana(modelo)
        frac = tokens / cap
        if st["ctx_nivel"] and frac < UMBRALES_CTX[st["ctx_nivel"] - 1] - 0.10:  # se compactó
            st["ctx_nivel"] = sum(frac >= x for x in UMBRALES_CTX)
        nivel = sum(frac >= x for x in UMBRALES_CTX)
        if nivel > st["ctx_nivel"]:
            st["ctx_nivel"] = nivel
            base = (f"Aviso de contexto (regla 3 del CLAUDE.md): este chat ocupa el {fmt(frac * 100, 0)} % de su "
                    f"ventana ({fmt(tokens / 1000, 0)} mil tokens de "
                    f"{'1 millón' if cap == 1_000_000 else fmt(cap / 1000, 0) + ' mil'}). ")
            msgs.append(base + (
                "Al pie de la respuesta de este trabajo va una línea nombrando el corte natural, y de acá en "
                "adelante el estado queda escrito a medida que se avanza." if nivel == 1 else
                "Al pie de la respuesta de este trabajo va un checkpoint armado: qué quedó terminado y qué falta. "
                "Si el usuario no dice nada, se sigue." if nivel == 2 else
                "Toca cerrar: terminá lo que está en curso y dejá el traspaso escrito (qué se hizo, qué falta, "
                "dónde está cada cosa) para seguir en un chat nuevo."))
    nivel_pts = sum(pts >= x for x in UMBRALES_PTS)
    if nivel_pts > st["pts_nivel"]:
        st["pts_nivel"] = nivel_pts
        base = (f"Aviso de costo (regla 3 del CLAUDE.md): este chat, con sus subagentes, ya gastó ≈ {fmt(pts)} "
                f"puntos de la cuota semanal (≈ {fmt(usd, 0)} USD a precio de lista). ")
        msgs.append(base + (
            "Decíselo al usuario en una línea al pie de la respuesta de este trabajo, con el corte natural más "
            "cercano." if nivel_pts == 1 else
            "Decíselo al usuario en una línea al pie y proponé cerrar este chat con el traspaso escrito: seguir "
            "acá es de lo más caro de la semana."))
    if msgs:
        msgs.append("No se pregunta «¿seguimos?» en un turno aparte.")

    tmp = ruta_st + ".tmp"
    with open(tmp, "w", encoding="utf-8") as h:
        json.dump(st, h)
    os.replace(tmp, ruta_st)
    limpiar_viejos()
    return " ".join(msgs) if msgs else None


def limpiar_viejos():
    """Los estados de chats sin uso hace más de 30 días se van (son solo marcas de qué se avisó)."""
    limite = time.time() - 30 * 86400
    for f in glob.glob(os.path.join(ESTADO_DIR, "*.json")):
        try:
            if os.path.getmtime(f) < limite:
                os.remove(f)
        except OSError:
            pass


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) == 3 and sys.argv[1] == "--probar":  # recorre un chat ya hecho, sin tocar estados reales
        global ESTADO_DIR
        import tempfile
        ESTADO_DIR = tempfile.mkdtemp()
        print(avisos({"transcript_path": sys.argv[2], "session_id": "prueba"}) or "(nada que avisar)")
        with open(os.path.join(ESTADO_DIR, "prueba.json"), encoding="utf-8") as h:
            st = json.load(h)
        usd = sum(v for f in st["archivos"].values() for v in f["ids"].values())
        print(f"[contexto {st['ctx'][0] if st['ctx'] else 0} tokens · {fmt(usd)} USD · "
              f"{fmt(usd / medidor()[1], 2)} pts · {len(st['archivos'])} archivos]")
        return
    try:
        entrada = json.load(sys.stdin)
        texto = avisos(entrada)
        if texto:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": entrada.get("hook_event_name"),
                                                     "additionalContext": texto}}, ensure_ascii=False))
    except Exception:
        pass  # un aviso roto no traba el chat
    sys.exit(0)


if __name__ == "__main__":
    main()
