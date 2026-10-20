"""Mide cuanto tarda crear y leer muchos archivos chicos (lo que el antivirus revisa al vuelo).

Uso: python bench_av.py <carpeta_destino> [repeticiones]
Imprime la mediana en ms de crear+leer 2000 archivos .py.
"""
import os
import shutil
import statistics
import sys
import time

destino = sys.argv[1]
reps = int(sys.argv[2]) if len(sys.argv) > 2 else 3
contenido = ("import os\n" + "x = 1\n" * 200).encode()
tiempos = []
for r in range(reps):
    carpeta = os.path.join(destino, f"bench_{os.getpid()}_{r}")
    os.makedirs(carpeta)
    t0 = time.perf_counter()
    for i in range(2000):
        with open(os.path.join(carpeta, f"m{i}.py"), "wb") as f:
            f.write(contenido)
    for i in range(2000):
        with open(os.path.join(carpeta, f"m{i}.py"), "rb") as f:
            f.read()
    tiempos.append((time.perf_counter() - t0) * 1000)
    shutil.rmtree(carpeta)
print(f"mediana {statistics.median(tiempos):.0f} ms  (corridas: {', '.join(f'{t:.0f}' for t in tiempos)})")
