"""Pruebas del módulo 3: rutas más cortas (Guías 9 y 10) y escenarios de Cusco."""

import math

import pytest

from src import enrutamiento_financiero as ef
from src import gestion_red as gr
from src.algoritmos.rutas_cortas import (bellman_ford, camino_floyd, ciclo_negativo_floyd,
                                         dijkstra, floyd_warshall, johnson, reconstruir_camino)
from src.graph import Grafo


def construir(aristas):
    g = Grafo(dirigido=True, ponderado=True)
    for u, v, w in aristas:
        for n in (u, v):
            if n not in g:
                g.agregar_nodo(n)
        g.agregar_arista(u, v, peso=w)
    return g


GUIA_9 = [("A", "B", 4), ("A", "C", 2), ("C", "D", 1), ("D", "B", 3), ("B", "E", 5), ("D", "E", 2)]
GUIA_10 = [("A", "B", 4), ("A", "C", 2), ("B", "D", 5), ("C", "D", 1), ("D", "E", 3),
           ("E", "X", 2), ("B", "X", 10), ("C", "E", 8)]


def test_dijkstra_ejemplo_guia_9():
    dist, ant = dijkstra(construir(GUIA_9), "A")
    assert dist["E"] == 5
    assert reconstruir_camino(ant, "E") == ["A", "C", "D", "E"]


def test_floyd_warshall_ejemplo_guia_10():
    orden, dist, sig = floyd_warshall(construir(GUIA_10))
    i, j = orden.index("A"), orden.index("X")
    assert dist[i][j] == 8
    assert camino_floyd(orden, sig, "A", "X") == ["A", "C", "D", "E", "X"]
    assert not ciclo_negativo_floyd(dist)


def test_johnson_coincide_con_floyd_warshall():
    g = construir(GUIA_10)
    orden, dist, _ = floyd_warshall(g)
    j = johnson(g)
    for a, u in enumerate(orden):
        for b, v in enumerate(orden):
            assert dist[a][b] == j[u][v]


def test_dijkstra_rechaza_pesos_negativos():
    with pytest.raises(ValueError):
        dijkstra(construir([("A", "B", -1)]), "A")


def test_bellman_ford_detecta_ciclo_negativo_guia_10():
    # Ejercicio 4 de la Guía 10: cashback D -> B (-25) crea un ciclo B -> D -> B
    g = construir(GUIA_10 + [("D", "B", -25), ("E", "C", -1)])
    _, _, ciclo = bellman_ford(g, "A")
    assert ciclo is not None and ciclo[0] == ciclo[-1]
    _, dist, _ = floyd_warshall(g)
    assert ciclo_negativo_floyd(dist)


def test_bellman_ford_con_pesos_negativos_sin_ciclo():
    g = construir([("A", "B", 4), ("A", "C", 5), ("C", "B", -3)])
    dist, _, ciclo = bellman_ford(g, "A")
    assert ciclo is None and dist["B"] == 2


@pytest.fixture(scope="module")
def red():
    return gr.cargar_red_enrutamiento()


def test_costo_aditivo_fijo_y_porcentual():
    assert ef.costo_arista({"comision_fija": 3.5, "comision_pct": 0.5}, 1000) == 8.5
    assert ef.costo_arista({"comision_fija": 0, "bonificacion": 4}, 400) == -4


@pytest.mark.parametrize("monto, criterio, camino, valor", [
    (5000, "costo", ["CTA_CMA_QUI", "CCE_DIF", "CTA_BX_LIMA"], 3.5),
    (5000, "tiempo", ["CTA_CMA_QUI", "CCE_INM", "CTA_BX_LIMA"], 8.0),
    (1500, "costo", ["CTA_CMA_QUI", "BILL_A", "CTA_BX_LIMA"], 2.25),
])
def test_escenario_quillabamba_lima(red, monto, criterio, camino, valor):
    r = ef.mejor_ruta(red, "CTA_CMA_QUI", "CTA_BX_LIMA", monto, criterio)
    assert r["camino"] == camino and r["costo"] == valor
    assert r["algoritmo"].startswith("Dijkstra")


def test_restriccion_de_limite(red):
    r = ef.mejor_ruta(red, "CTA_CMA_QUI", "CTA_BX_LIMA", 50000, "tiempo")
    assert "CCE_INM" not in r["camino"]


def test_turista_y_cliente(red):
    assert ef.mejor_ruta(red, "TC_EXT", "CTA_REST_MPP", 300)["costo"] == 10.5
    assert ef.mejor_ruta(red, "TD_CMA_CUS", "EFECTIVO_CLIENTE", 200)["costo"] == 0
    rapido = ef.mejor_ruta(red, "TD_CMA_CUS", "EFECTIVO_CLIENTE", 200, "tiempo")
    assert "ATM_RED_CERCA" in rapido["camino"]


def test_alternativas_ordenadas(red):
    viables, no_viables = ef.rutas_alternativas(red, "CTA_CMA_QUI", "CTA_BX_LIMA", 5000)
    costos = [r["costo"] for r in viables]
    assert costos == sorted(costos) and len(viables) >= 4
    assert all(r["restricciones"] for r in no_viables)


def test_promocion_usa_bellman_ford():
    r = ef.mejor_ruta(gr.cargar_red_enrutamiento("promo"), "CTA_CMA_QUI", "CTA_BX_LIMA", 400)
    assert r["algoritmo"].startswith("Bellman-Ford") and r["costo"] == -4


def test_ruleteo():
    rul = ef.detectar_ruleteo(gr.cargar_red_enrutamiento("ruleteo"), 400)
    assert rul["costo_por_vuelta"] == -3
    assert ef.detectar_ruleteo(gr.cargar_red_enrutamiento(), 400) is None


def test_matriz_de_tiempos_floyd_y_johnson():
    fisica = gr.cargar_red_fisica()
    f = ef.matriz_tiempos(fisica, "floyd")
    j = ef.matriz_tiempos(fisica, "johnson")
    assert math.isclose(f["ATM_PLZ"]["ATM_MPP"], 4.35)
    assert all(math.isclose(f[u][v], j[u][v]) for u in f for v in f[u])
