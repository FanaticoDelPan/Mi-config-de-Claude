"""¿Los subagentes rinden peor con la memoria llena? Señales de los registros de 14 días, por tramo de contexto:
- herramienta que falla (is_error), y en particular Edit que no encuentra el texto (se acordaba mal del archivo);
- relectura de un archivo que ya había leído y no tocó desde entonces.
Más una simulación de cuánto se ahorra partir un agente largo en dos."""
import glob, json, os, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = os.path.expanduser("~/.claude/projects")
desde = (datetime.now(timezone.utc) - timedelta(days=14)).timestamp()
TRAMOS = [(0, 100e3), (100e3, 200e3), (200e3, 300e3), (300e3, 400e3), (400e3, 1e9)]
LEER = 0.20 / 1e6  # Opus 5.5, lectura de caché, USD por token
ESCRIBIR = 4 * 1.25 / 1e6
PT = 1769 / 66.5


def tramo(c):
    for i, (a, b) in enumerate(TRAMOS):
        if a <= c < b:
            return i


est = defaultdict(lambda: defaultdict(int))
vistos = set()
agentes = []  # secuencias de contexto por agente, para la simulación
for f in glob.glob(os.path.join(RAIZ, "**", "subagents", "*.jsonl"), recursive=True):
    if os.path.getmtime(f) < desde:
        continue
    usos = {}  # tool_use_id -> (nombre, ruta, contexto)
    ctx_act, leidos, ctxs, ids = 0, set(), [], set()
    for linea in open(f, encoding="utf-8", errors="ignore"):
        try:
            d = json.loads(linea)
        except ValueError:
            continue
        m = d.get("message") or {}
        cont = m.get("content")
        if d.get("type") == "assistant":
            if m.get("id") in vistos:
                continue
            u = m.get("usage") or {}
            c = sum(u.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
            if c:
                ctx_act = c
                if m.get("id") not in ids:
                    ids.add(m.get("id"))
                    ctxs.append(c)
            for b in cont if isinstance(cont, list) else []:
                if b.get("type") != "tool_use":
                    continue
                inp = b.get("input") or {}
                ruta = (inp.get("file_path") or "").lower()
                usos[b["id"]] = (b.get("name"), ruta, ctx_act)
                t = tramo(ctx_act)
                est[t]["usos"] += 1
                if b.get("name") == "Read" and ruta:
                    est[t]["lecturas"] += 1
                    pedazo = (ruta, inp.get("offset"), inp.get("limit"))  # otra parte del mismo archivo no cuenta
                    if pedazo in leidos:
                        est[t]["relecturas"] += 1
                    leidos.add(pedazo)
                elif b.get("name") in ("Edit", "Write") and ruta:
                    est[t]["ediciones"] += 1
                    leidos = {p for p in leidos if p[0] != ruta}  # releer lo que se acaba de cambiar es legítimo
        elif d.get("type") == "user":
            for b in cont if isinstance(cont, list) else []:
                if b.get("type") != "tool_result" or b.get("tool_use_id") not in usos:
                    continue
                nom, ruta, c = usos.pop(b["tool_use_id"])
                t = tramo(c)
                if b.get("is_error"):
                    est[t]["fallas"] += 1
                    txt = json.dumps(b.get("content"))[:400].lower()
                    if nom == "Edit" and "not found" in txt:
                        est[t]["edit_no_encontro"] += 1
    vistos.update(ids)
    if ctxs:
        agentes.append(ctxs)

print(f"Agentes de 14 días: {len(agentes)}\n")
print("tramo de contexto     usos   fallas   edits-sin-texto/edits   relecturas/lecturas")
for i, (a, b) in enumerate(TRAMOS):
    e = est[i]
    if not e["usos"]:
        continue
    nom = f"{a/1e3:.0f}-{b/1e3:.0f}k" if b < 1e9 else f">{a/1e3:.0f}k"
    print(f"  {nom:12} {e['usos']:9}   {e['fallas']/e['usos']*100:5.1f} %   "
          f"{e['edit_no_encontro']:4}/{e['ediciones']:<5} = {e['edit_no_encontro']/max(e['ediciones'],1)*100:4.1f} %   "
          f"{e['relecturas']:4}/{e['lecturas']:<5} = {e['relecturas']/max(e['lecturas'],1)*100:4.1f} %")

# Simulación: cada agente que pasa de TOPE se parte donde lo cruza; el que sigue arranca con el contexto
# inicial del original más RELEER tokens de archivos que tiene que volver a leer (que se pagan como escritura).
print("\nSimulación de partir los agentes largos (lectura de caché + lo que hay que releer):")
for tope in (250e3, 350e3):
    for releer in (50e3, 100e3):
        ahorro = n = 0
        for ctxs in agentes:
            if max(ctxs) <= tope:
                continue
            n += 1
            base, k = ctxs[0], next(i for i, c in enumerate(ctxs) if c > tope)
            corte = ctxs[k - 1] if k else ctxs[0]
            baja = corte - base - releer  # cuánto menos contexto carga cada turno de la segunda mitad
            ahorro += baja * LEER * (len(ctxs) - k) - releer * ESCRIBIR - base * ESCRIBIR
        print(f"  partir al pasar {tope/1e3:.0f}k, releyendo {releer/1e3:.0f}k: {n} agentes, ahorro {ahorro/PT:5.1f} pts en 14 días")
