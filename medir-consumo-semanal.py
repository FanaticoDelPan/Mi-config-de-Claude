"""Consumo de Claude Code en una semana de cuota, a precio de lista (equivalente, no facturado).

Uso:  python medir-consumo-semanal.py                          (la semana en curso, con la línea de HOY)
      python medir-consumo-semanal.py 2026-09-16 [porcentaje_usado]
      (la fecha es el miércoles del REINICIO que abre la semana; el reinicio es a las 19:00 de Argentina)
      --sin-subir   no guarda ni sube el consumo de esta PC (para pruebas)

Sale: total en USD y puntos, por tramo de 24 h desde el reinicio, por proyecto, subagentes y los chats por tamaño.
Con el porcentaje final de la semana recalibra cuántos USD/tokens vale un punto.
Las dos PC del dueño comparten la cuota: cada corrida deja el consumo de ESTA PC (por tramo y proyecto, esta semana
y la anterior) en consumo/<PC>.json, lo sube, y suma lo que dejó la otra. Lo de hoy, los subagentes y los chats por
tamaño son solo de esta PC. El hook de arranque (check-symlink.ps1) lo corre de fondo si pasaron más de 2 días.
La línea de base (semana 9/9 -> 16/9, 97 %): 33 USD y 48,6M tokens por punto; 292 subagentes (37 %);
chats (todos los proyectos): consulta n=30 0,09 pt · chico n=42 0,44 · mediano n=19 1,46 (4,1 agentes)
· grande n=11 4,37 (13,6 agentes; 48 de los 97 puntos).
"""
import glob
import json
import os
import platform
import statistics as st
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

AR = timezone(timedelta(hours=-3))
USD_POR_PUNTO = 26.6  # 28/10, cierre de la semana del 21/10 al 87 %, las dos PC sumadas (66,7M tokens/pt). Antes:
                      # 29,6 el 25/09 (mitad de semana al 36 %, una sola PC); 35 y 33 se midieron con la salida
                      # subcontada y sin la escritura de caché de 1 hora
RAIZ = os.path.expanduser("~/.claude/projects")
REPO = os.path.dirname(os.path.abspath(__file__))
CARPETA_PC = os.path.join(REPO, "consumo")
PC = os.environ.get("COMPUTERNAME") or platform.node() or "pc"
NOMBRES_PC = {"DESKTOP-1FBVMK9": "casa", "NOTEBOOKJOA": "oficina"}
DIAS_GUARDADOS = 70


def nombre_pc(pc):
    return NOMBRES_PC.get(pc, pc)


def git(*args):
    """(salió bien, salida). Sin pedir credenciales: sin conexión, falla y sigue."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    try:
        r = subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True, timeout=30, env=env)
        return r.returncode == 0, r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return False, ""


def traer_repo():
    """Trae lo que subió la otra PC. Si hay commits de los dos lados y los de acá son solo de consumo/, los pone
    arriba (no chocan: cada PC escribe su archivo); si hay otra cosa, no toca nada (lo avisa el hook de arranque)."""
    if not git("fetch", "--quiet")[0] or git("merge", "--ff-only", "--quiet", "@{u}")[0]:
        return
    ok, propios = git("diff", "--name-only", "@{u}...HEAD")
    if ok and all(l.startswith("consumo/") for l in propios.split()):
        if not git("rebase", "--autostash", "--quiet", "@{u}")[0]:
            git("rebase", "--abort")


def guardar_pc(desde, hasta, mio):
    """Reemplaza en consumo/<PC>.json los tramos de [desde, hasta) y, si cambió algo, lo commitea solo y lo sube."""
    os.makedirs(CARPETA_PC, exist_ok=True)
    ruta = os.path.join(CARPETA_PC, f"{PC}.json")
    try:
        with open(ruta, encoding="utf-8") as fh:
            viejo = json.load(fh).get("tramos", {})
    except (OSError, ValueError):
        viejo = {}
    d0, d1 = desde.date().isoformat(), hasta.date().isoformat()
    corte = (datetime.now(AR) - timedelta(days=DIAS_GUARDADOS)).date().isoformat()
    tramos = {k: v for k, v in viejo.items() if k >= corte and not d0 <= k < d1}
    for (k, proy), (usd, tok, usd_sub, subs) in mio.items():
        tramos.setdefault(k, {})[proy] = {"usd": round(usd, 2), "tok": int(tok), "usd_sub": round(usd_sub, 2),
                                          "subs": len(subs)}
    if tramos == viejo:
        os.utime(ruta)  # el hook mira la fecha del archivo para no correrlo en cada chat
        return
    ahora = datetime.now(AR)
    with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"pc": PC, "actualizado": ahora.isoformat(timespec="minutes"), "tramos": tramos}, fh,
                  ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    rel = f"consumo/{PC}.json"
    git("add", "--", rel)
    if git("commit", "-q", "-m", f"consumo: {nombre_pc(PC)} al {ahora:%d/%m %H:%M}", "--", rel)[0]:
        git("push", "-q")


def otras_pc():
    for ruta in sorted(glob.glob(os.path.join(CARPETA_PC, "*.json"))):
        try:
            with open(ruta, encoding="utf-8") as fh:
                datos = json.load(fh)
        except (OSError, ValueError):
            continue
        if datos.get("pc") != PC:
            yield datos


def precio(modelo):
    """(entrada, lectura de caché, salida) en USD por millón. La escritura de caché sale de la entrada:
    x1,25 la de 5 minutos y x2 la de 1 hora (Claude Code usa las dos)."""
    modelo = modelo or ""
    if "haiku" in modelo:
        return (1, 0.10, 5)
    if "sonnet-5" in modelo:
        return (2, 0.20, 10)
    if "sonnet" in modelo:
        return (3, 0.30, 15)
    if "fable" in modelo or "mythos" in modelo:
        return (10, 0.25, 50)
    if "opus-5-5" in modelo:
        return (4, 0.20, 20)
    return (5, 0.50, 25)  # Opus 5 y anteriores


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # la consola de Windows es cp1252
    ahora = datetime.now(AR)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    subir = "--sin-subir" not in sys.argv
    if args:
        t0 = datetime.fromisoformat(args[0]).replace(hour=19, tzinfo=AR)
    else:  # el último reinicio: miércoles 19:00
        t0 = (ahora - timedelta(days=(ahora.weekday() - 2) % 7)).replace(hour=19, minute=0, second=0, microsecond=0)
        if t0 > ahora:
            t0 -= timedelta(days=7)
    t1 = t0 + timedelta(days=7)
    e0 = t0 - timedelta(days=7)  # la semana anterior se lee solo para guardarla completa para la otra PC
    hoy0 = max(ahora.replace(hour=0, minute=0, second=0, microsecond=0), t0)
    hoy_tok, hoy_subs = 0.0, set()
    pct = float(args[1]) if len(args) > 1 else None

    mensajes = {}
    total = tokens = 0.0
    por_dia, por_proy = defaultdict(float), defaultdict(float)
    tramo_tok, tramo_sub = defaultdict(float), defaultdict(float)
    chats = defaultdict(lambda: {"chat": 0.0, "sub": 0.0, "subs": set(), "ini": None, "ctx": 0})
    for f in glob.glob(os.path.join(RAIZ, "**", "*.jsonl"), recursive=True):
        if os.path.getmtime(f) < e0.timestamp():
            continue
        partes = os.path.relpath(f, RAIZ).split(os.sep)
        proy = partes[0]
        sesion = partes[1][:-6] if len(partes) == 2 else partes[1]
        es_sub = "subagents" in partes
        for linea in open(f, encoding="utf-8", errors="ignore"):
            if '"usage"' not in linea:
                continue
            try:
                d = json.loads(linea)
            except ValueError:
                continue
            m = d.get("message") or {}
            u = m.get("usage")
            if d.get("type") != "assistant" or not u or not d.get("timestamp"):
                continue
            ts = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")).astimezone(AR)
            if not e0 <= ts < t1:
                continue
            # Un mismo mensaje se escribe en varias líneas (una por bloque) y las primeras traen la salida
            # a medio contar: se queda la de salida más alta. Quedarse con la primera subcontaba ~40 %.
            clave = m.get("id") or id(d)
            previo = mensajes.get(clave)
            if previo is None or (u.get("output_tokens") or 0) > (previo[0].get("output_tokens") or 0):
                mensajes[clave] = (u, m.get("model"), ts, proy, sesion, es_sub, f)

    mio = defaultdict(lambda: [0.0, 0.0, 0.0, set()])  # (tramo, proyecto) -> USD, tokens, USD de agentes, agentes
    for u, modelo, ts, proy, sesion, es_sub, f in mensajes.values():
            p = precio(modelo)
            a, b, r, o = (u.get(k) or 0 for k in
                          ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))
            cc = u.get("cache_creation") or {}
            b1h = min(cc.get("ephemeral_1h_input_tokens") or 0, b)
            usd = (a * p[0] + (b - b1h) * p[0] * 1.25 + b1h * p[0] * 2 + r * p[1] + o * p[2]) / 1e6
            g = mio[((ts - timedelta(hours=19)).date().isoformat(), proy)]  # el tramo se nombra por el día que abre
            g[0] += usd
            g[1] += a + b + r + o
            if es_sub:
                g[2] += usd
                g[3].add(f)
            if ts < t0:
                continue
            total += usd
            tokens += a + b + r + o
            n = int((ts - t0) // timedelta(days=1))  # tramo de 24 h contado desde el reinicio
            por_dia[n] += usd
            tramo_tok[n] += a + b + r + o
            if es_sub:
                tramo_sub[n] += usd
            por_proy[proy] += usd
            if ts >= hoy0:
                hoy_tok += a + b + r + o
                if es_sub:
                    hoy_subs.add(f)
            c = chats[(proy, sesion)]
            if es_sub:
                c["sub"] += usd
                c["subs"].add(f)
            else:
                c["chat"] += usd
                c["ctx"] = max(c["ctx"], a + b + r)
                c["ini"] = min(c["ini"] or ts, ts)

    # La otra PC: se suma a la semana, los tramos y los proyectos (la cuota es una sola).
    if subir:
        traer_repo()
        guardar_pc(e0, t1, mio)
    por_pc = {nombre_pc(PC): (total, tokens, None)}
    proy_pc = defaultdict(dict)
    for k, v in por_proy.items():
        proy_pc[k][nombre_pc(PC)] = v
    for datos in otras_pc():
        nom, usd_pc, tok_pc = nombre_pc(datos.get("pc", "?")), 0.0, 0.0
        for k, proys in datos.get("tramos", {}).items():
            n = (date.fromisoformat(k) - t0.date()).days
            if not 0 <= n < 7:
                continue
            for proy, v in proys.items():
                usd_pc += v["usd"]
                tok_pc += v["tok"]
                por_dia[n] += v["usd"]
                tramo_tok[n] += v["tok"]
                tramo_sub[n] += v["usd_sub"]
                por_proy[proy] += v["usd"]
                proy_pc[proy][nom] = proy_pc[proy].get(nom, 0.0) + v["usd"]
        total += usd_pc
        tokens += tok_pc
        por_pc[nom] = (usd_pc, tok_pc, datos.get("actualizado"))

    pt = lambda usd: usd / USD_POR_PUNTO
    print(f"Semana {t0:%d/%m %H:%M} -> {t1:%d/%m %H:%M}: {total:.0f} USD = {pt(total):.1f} pts, {tokens/1e6:.0f}M tokens")
    if len(por_pc) > 1:
        print("  " + " · ".join(f"{nom}: {u:.0f} USD, {t/1e6:.0f}M tok"
                                + (f" (datos al {datetime.fromisoformat(a):%d/%m %H:%M})" if a else " (esta PC)")
                                for nom, (u, t, a) in por_pc.items()))
    else:
        print("  Solo esta PC: la otra todavía no dejó su consumo en el repo (carpeta consumo/).")
    if t0 <= ahora < t1:
        print(f"  Hoy en esta PC desde las {hoy0:%H:%M}: {hoy_tok/1e6:.0f}M tokens, {len(hoy_subs)} subagentes")
    if pct:
        print(f"  Recalibrado con {pct} %: {total/pct:.1f} USD/pt, {tokens/pct/1e6:.1f}M tokens/pt")
    # Tramos de 24 h desde el reinicio (miércoles 19:00) contra la línea de ritmo: 16 % por día de trabajo,
    # sábado y domingo cuentan como uno (8 + 8), 4 de margen. Con el % real, cada tramo recibe su parte
    # proporcional al gasto; sin él, se estima con USD_POR_PUNTO.
    linea = (16, 32, 40, 48, 64, 80, 96)
    print("\nPor tramo de 24 h desde el reinicio (acumulado contra la línea de 16 %/día, finde = 1 día):")
    acum = 0.0
    for n in sorted(por_dia):
        ini = t0 + timedelta(days=n)
        cuota = por_dia[n] / total * pct if pct else pt(por_dia[n])
        acum += cuota
        print(f"  día {n+1}  {ini:%a %d/%m %H:%M} -> {ini + timedelta(days=1):%a %d/%m %H:%M}"
              f"  {cuota:5.1f} %  {tramo_tok[n]/1e6:4.0f}M tok  agentes {tramo_sub[n]/por_dia[n]*100:3.0f} %"
              f"  acumulado {acum:5.1f} / línea {linea[min(n, 6)]}")
    print("\nPor proyecto (los worktrees van aparte):")
    for k, v in sorted(por_proy.items(), key=lambda x: -x[1]):
        if pt(v) >= 0.5:
            reparto = ", ".join(f"{n} {pt(x):.1f}" for n, x in proy_pc[k].items()) if len(por_pc) > 1 else ""
            print(f"  {pt(v):5.1f} pts  {k}" + (f"  ({reparto})" if reparto else ""))
    subs = sum(len(c["subs"]) for c in chats.values())
    usd_subs = sum(c["sub"] for c in chats.values())
    if subs:
        print(f"\nSubagentes en esta PC: {subs}, {usd_subs/subs:.1f} USD c/u, {usd_subs/por_pc[nombre_pc(PC)][0]*100:.0f} % de su gasto")

    print("\nChats por tamaño, solo esta PC (costo del chat + sus subagentes):")
    filas = [c for c in chats.values() if c["ini"]]
    for nombre, lo, hi in (("consulta", 0, 0.2), ("chico", 0.2, 1), ("mediano", 1, 2.5), ("grande", 2.5, 1e9)):
        g = [c for c in filas if lo <= pt(c["chat"] + c["sub"]) < hi]
        if not g:
            continue
        costos = [pt(c["chat"] + c["sub"]) for c in g]
        print(f"  {nombre:9} n={len(g):3}  total={sum(costos):5.1f}  media={st.mean(costos):4.2f} pts"
              f"  agentes={st.mean(len(c['subs']) for c in g):4.1f}  contexto máx (mediana)={st.median(c['ctx'] for c in g)//1000}k")


if __name__ == "__main__":
    main()
