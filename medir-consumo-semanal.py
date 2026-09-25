"""Consumo de Claude Code en una semana de cuota, a precio de lista (equivalente, no facturado).

Uso:  python medir-consumo-semanal.py                          (la semana en curso, con la línea de HOY)
      python medir-consumo-semanal.py 2026-09-16 [porcentaje_usado]
      (la fecha es el miércoles del REINICIO que abre la semana; el reinicio es a las 19:00 de Argentina)

Sale: total en USD y puntos, por tramo de 24 h desde el reinicio, por proyecto, subagentes y los chats por tamaño.
Con el porcentaje final de la semana recalibra cuántos USD/tokens vale un punto.
La línea de base (semana 9/9 -> 16/9, 97 %): 33 USD y 48,6M tokens por punto; 292 subagentes (37 %);
chats (todos los proyectos): consulta n=30 0,09 pt · chico n=42 0,44 · mediano n=19 1,46 (4,1 agentes)
· grande n=11 4,37 (13,6 agentes; 48 de los 97 puntos).
"""
import glob
import json
import os
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

AR = timezone(timedelta(hours=-3))
USD_POR_PUNTO = 25.6  # 25/09, mitad de semana al 36 %, casi todo Opus 5.5 (antes 35 y 33)
RAIZ = os.path.expanduser("~/.claude/projects")


def precio(modelo):
    modelo = modelo or ""
    if "haiku" in modelo:
        return (1, 1.25, 0.10, 5)
    if "sonnet" in modelo:
        return (3, 3.75, 0.30, 15)
    if "opus-5-5" in modelo:
        return (4, 5, 0.20, 20)
    return (5, 6.25, 0.50, 25)  # Opus (y Fable valuado como Opus: es un piso)


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # la consola de Windows es cp1252
    ahora = datetime.now(AR)
    if len(sys.argv) > 1:
        t0 = datetime.fromisoformat(sys.argv[1]).replace(hour=19, tzinfo=AR)
    else:  # el último reinicio: miércoles 19:00
        t0 = (ahora - timedelta(days=(ahora.weekday() - 2) % 7)).replace(hour=19, minute=0, second=0, microsecond=0)
        if t0 > ahora:
            t0 -= timedelta(days=7)
    t1 = t0 + timedelta(days=7)
    hoy0 = max(ahora.replace(hour=0, minute=0, second=0, microsecond=0), t0)
    hoy_tok, hoy_subs = 0.0, set()
    pct = float(sys.argv[2]) if len(sys.argv) > 2 else None

    vistos = set()
    total = tokens = 0.0
    por_dia, por_proy = defaultdict(float), defaultdict(float)
    tramo_tok, tramo_sub = defaultdict(float), defaultdict(float)
    chats = defaultdict(lambda: {"chat": 0.0, "sub": 0.0, "subs": set(), "ini": None, "ctx": 0})
    for f in glob.glob(os.path.join(RAIZ, "**", "*.jsonl"), recursive=True):
        if os.path.getmtime(f) < t0.timestamp():
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
            if d.get("type") != "assistant" or not u or not d.get("timestamp") or m.get("id") in vistos:
                continue
            ts = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")).astimezone(AR)
            if not t0 <= ts < t1:
                continue
            vistos.add(m.get("id"))
            p = precio(m.get("model"))
            a, b, r, o = (u.get(k) or 0 for k in
                          ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))
            usd = (a * p[0] + b * p[1] + r * p[2] + o * p[3]) / 1e6
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

    pt = lambda usd: usd / USD_POR_PUNTO
    print(f"Semana {t0:%d/%m %H:%M} -> {t1:%d/%m %H:%M}: {total:.0f} USD = {pt(total):.1f} pts, {tokens/1e6:.0f}M tokens")
    if t0 <= ahora < t1:
        print(f"  Hoy desde las {hoy0:%H:%M}: {hoy_tok/1e6:.0f}M tokens, {len(hoy_subs)} subagentes")
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
            print(f"  {pt(v):5.1f} pts  {k}")
    subs = sum(len(c["subs"]) for c in chats.values())
    usd_subs = sum(c["sub"] for c in chats.values())
    if subs:
        print(f"\nSubagentes: {subs}, {usd_subs/subs:.1f} USD c/u, {usd_subs/total*100:.0f} % del gasto")

    print("\nChats por tamaño (costo del chat + sus subagentes):")
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
