"""Funciones auxiliares compartidas: rutas, lectura de CSV, tablas y medición."""

import csv
import math
import os
import sys
import time
import tracemalloc

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(RAIZ, "data")
REPORTES_DIR = os.path.join(RAIZ, "reportes")

# Los recorridos DFS recursivos (como en la Guía 7) pueden superar el límite
# por defecto de Python (1000) en las redes sintéticas grandes del módulo 5.
sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))


def ruta_datos(nombre):
    return os.path.join(DATA_DIR, nombre)


def ruta_reporte(nombre):
    os.makedirs(REPORTES_DIR, exist_ok=True)
    return os.path.join(REPORTES_DIR, nombre)


def a_numero(valor):
    """Convierte texto a int o float. Devuelve el texto si no es numérico y
    None si está vacío."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return valor
    texto = str(valor).strip()
    if texto == "":
        return None
    try:
        numero = float(texto)
    except ValueError:
        return texto
    if math.isfinite(numero) and numero.is_integer() and "." not in texto:
        return int(numero)
    return numero


def leer_csv(ruta):
    """Lee un CSV con encabezado y devuelve una lista de diccionarios con los
    valores numéricos ya convertidos."""
    with open(ruta, newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        filas = []
        for fila in lector:
            filas.append({k.strip(): a_numero(v) for k, v in fila.items() if k})
        return filas


def escribir_csv(ruta, filas, encabezados=None):
    if encabezados is None:
        encabezados = list(filas[0].keys()) if filas else []
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=encabezados, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(filas)


def formatear_tabla(filas, encabezados):
    """Tabla de texto alineada. ``filas`` es una lista de listas."""
    texto = [[str(c) for c in encabezados]] + [[_fmt(c) for c in f] for f in filas]
    anchos = [max(len(f[i]) for f in texto) for i in range(len(encabezados))]
    lineas = []
    for k, fila in enumerate(texto):
        lineas.append("  ".join(c.ljust(anchos[i]) for i, c in enumerate(fila)))
        if k == 0:
            lineas.append("  ".join("-" * a for a in anchos))
    return "\n".join(lineas)


def _fmt(valor):
    if isinstance(valor, float):
        if math.isinf(valor):
            return "INF"
        return f"{valor:,.2f}"
    return str(valor)


def guardar_texto(nombre, contenido):
    ruta = ruta_reporte(nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)
    return ruta


def medir(funcion, *args, **kwargs):
    """Ejecuta ``funcion`` y devuelve (resultado, segundos, memoria_pico_KB).

    El tiempo se mide con time.perf_counter y la memoria con tracemalloc, en
    dos ejecuciones separadas para que el rastreo de memoria no distorsione
    el tiempo."""
    inicio = time.perf_counter()
    resultado = funcion(*args, **kwargs)
    segundos = time.perf_counter() - inicio

    tracemalloc.start()
    funcion(*args, **kwargs)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return resultado, segundos, pico / 1024
