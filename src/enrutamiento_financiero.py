"""Módulo 3 – Optimización del enrutamiento de operaciones y cálculo de comisiones.

Modelo de costo (problemática, sección 5.4 a):
    las comisiones se cobran aparte al ordenante y el monto llega íntegro, así
    que el costo de usar un canal para enviar un monto M es aditivo:

        w(u, v) = comision_fija + comision_pct / 100 * M - bonificacion

Selección del algoritmo:
- Dijkstra si todos los pesos son >= 0 (caso normal).
- Bellman-Ford si alguna bonificación vuelve negativo un peso; además detecta
  ciclos negativos ("ruleteo" de promociones).
- Enumeración DFS con poda para listar rutas alternativas.
- Floyd-Warshall (red pequeña) o Johnson (red grande y dispersa) para la matriz
  de tiempos entre todas las ciudades.
"""

import math

from src.algoritmos.recorridos import caminos_simples
from src.algoritmos.rutas_cortas import (bellman_ford, dijkstra, floyd_warshall,
                                         johnson, reconstruir_camino)
from src.utils import formatear_tabla

ESCENARIOS = [
    ("Comerciante de café en Quillabamba paga a su proveedor en Lima",
     "CTA_CMA_QUI", "CTA_BX_LIMA", 5000),
    ("Pago pequeño del mismo comerciante a su proveedor",
     "CTA_CMA_QUI", "CTA_BX_LIMA", 1500),
    ("Pago grande que supera el límite de la transferencia inmediata",
     "CTA_CMA_QUI", "CTA_BX_LIMA", 50000),
    ("Turista paga con tarjeta extranjera en un restaurante de Machupicchu Pueblo",
     "TC_EXT", "CTA_REST_MPP", 300),
    ("Cliente de Cusco retira efectivo con su tarjeta de débito",
     "TD_CMA_CUS", "EFECTIVO_CLIENTE", 200),
]


# ------------------------------------------------------------------ pesos
def peso_operacion(monto, criterio="costo"):
    """Función de peso para un monto y un criterio ("costo" o "tiempo")."""
    if criterio == "tiempo":
        return lambda u, v, a: a.get("tiempo_min", 0)
    if criterio != "costo":
        raise ValueError("El criterio debe ser 'costo' o 'tiempo'.")
    return lambda u, v, a: (a.get("comision_fija", 0)
                            + a.get("comision_pct", 0) / 100 * monto
                            - a.get("bonificacion", 0))


def costo_arista(atributos, monto):
    return peso_operacion(monto, "costo")(None, None, atributos)


def _permitida(atributos, monto):
    limite = atributos.get("limite")
    return atributos.get("disponible", 1) == 1 and (limite is None or limite >= monto)


def red_habilitada(grafo, monto):
    """Excluye los canales no disponibles o cuyo límite es menor que el monto."""
    return grafo.filtrar_aristas(lambda u, v, a: _permitida(a, monto))


def resumir_camino(grafo, camino, monto):
    costo = tiempo = 0
    canales = []
    restricciones = []
    for u, v in zip(camino, camino[1:]):
        a = grafo.atributos_arista(u, v)
        costo += costo_arista(a, monto)
        tiempo += a.get("tiempo_min", 0)
        canales.append(a.get("canal", f"{u}->{v}"))
        if not _permitida(a, monto):
            restricciones.append(f"{a.get('canal', u + '->' + v)} (límite {a.get('limite')})")
    return {"camino": camino, "costo": round(costo, 2), "tiempo_min": tiempo,
            "canales": canales, "restricciones": restricciones}


# ------------------------------------------------------------- consultas
def mejor_ruta(grafo, origen, destino, monto, criterio="costo"):
    """Ruta óptima según el criterio. Elige el algoritmo según los pesos."""
    red = red_habilitada(grafo, monto)
    w = peso_operacion(monto, criterio)
    hay_negativos = any(w(u, v, a) < 0 for u, v, a in red.aristas())
    if hay_negativos:
        _, anteriores, ciclo = bellman_ford(red, origen, w)
        algoritmo = "Bellman-Ford (hay pesos negativos por bonificaciones)"
        if ciclo:
            return {"algoritmo": algoritmo, "camino": [], "ciclo_negativo": ciclo,
                    "costo": -math.inf, "tiempo_min": None, "canales": [],
                    "restricciones": []}
    else:
        _, anteriores = dijkstra(red, origen, w)
        algoritmo = "Dijkstra (todos los pesos son no negativos)"
    camino = reconstruir_camino(anteriores, destino)
    resultado = resumir_camino(grafo, camino, monto) if camino else {
        "camino": [], "costo": math.inf, "tiempo_min": math.inf, "canales": [],
        "restricciones": []}
    resultado["algoritmo"] = algoritmo
    resultado["ciclo_negativo"] = None
    return resultado


def rutas_alternativas(grafo, origen, destino, monto, criterio="costo", k=6,
                       max_saltos=6):
    """Rutas alternativas (DFS con poda) sobre los canales disponibles.
    Las rutas que violan un límite se listan al final como no viables."""
    disponibles = grafo.filtrar_aristas(lambda u, v, a: a.get("disponible", 1) == 1)
    w = peso_operacion(monto, criterio)
    encontrados = caminos_simples(disponibles, origen, destino, w, max_saltos, None)
    rutas = [resumir_camino(grafo, camino, monto) for _, camino in encontrados]
    clave = "costo" if criterio == "costo" else "tiempo_min"
    viables = sorted((r for r in rutas if not r["restricciones"]), key=lambda r: r[clave])
    no_viables = sorted((r for r in rutas if r["restricciones"]), key=lambda r: r[clave])
    return viables[:k], no_viables


def detectar_ruleteo(grafo, monto):
    """Busca ciclos negativos en toda la red (Bellman-Ford desde un nodo
    auxiliar). Un ciclo negativo significa que repetir esas operaciones genera
    ganancia: posible abuso de una promoción ("ruleteo")."""
    red = red_habilitada(grafo, monto)
    w = peso_operacion(monto, "costo")
    _, _, ciclo = bellman_ford(red, None, w)
    if not ciclo:
        return None
    costo = sum(w(u, v, red.atributos_arista(u, v)) for u, v in zip(ciclo, ciclo[1:]))
    return {"ciclo": ciclo, "costo_por_vuelta": round(costo, 2)}


def matriz_tiempos(red_fisica, algoritmo="floyd"):
    """Tiempo mínimo de viaje (horas) entre todos los pares de la red física.
    Devuelve {origen: {destino: horas}}."""
    if algoritmo == "johnson":
        return johnson(red_fisica, "tiempo_h")
    orden, dist, _ = floyd_warshall(red_fisica, "tiempo_h")
    return {u: {v: dist[i][j] for j, v in enumerate(orden)} for i, u in enumerate(orden)}


# ---------------------------------------------------------------- reporte
def _linea_ruta(r):
    return [" -> ".join(r["camino"]), f"S/ {r['costo']:,.2f}", f"{r['tiempo_min']} min",
            "; ".join(r["canales"])]


def reporte_operacion(grafo, origen, destino, monto, titulo=None):
    lineas = []
    lineas.append("=" * 90)
    lineas.append(titulo or f"Operación {origen} -> {destino}")
    lineas.append(f"Monto: S/ {monto:,.2f}")
    lineas.append("=" * 90)
    for criterio in ("costo", "tiempo"):
        r = mejor_ruta(grafo, origen, destino, monto, criterio)
        lineas.append(f"\nMejor ruta por {criterio} — algoritmo: {r['algoritmo']}")
        if r.get("ciclo_negativo"):
            lineas.append("  ALERTA: ciclo negativo (ruleteo): " + " -> ".join(r["ciclo_negativo"]))
            lineas.append("  Las rutas mínimas no están definidas mientras exista el ciclo.")
            continue
        if not r["camino"]:
            lineas.append("  No existe ruta viable para ese monto.")
            continue
        lineas.append("  Ruta:     " + " -> ".join(r["camino"]))
        lineas.append(f"  Comisión: S/ {r['costo']:,.2f}    Tiempo: {r['tiempo_min']} min")
        lineas.append("  Canales:  " + "; ".join(r["canales"]))
    viables, no_viables = rutas_alternativas(grafo, origen, destino, monto)
    lineas.append("\nAlternativas viables ordenadas por comisión (enumeración DFS con poda):")
    lineas.append(formatear_tabla([_linea_ruta(r) for r in viables],
                                  ["Ruta", "Comisión", "Tiempo", "Canales"]))
    if no_viables:
        lineas.append("\nRutas descartadas por restricciones de límite:")
        for r in no_viables:
            lineas.append("  " + " -> ".join(r["camino"]) + "  | excede: "
                          + ", ".join(r["restricciones"]))
    return "\n".join(lineas)
