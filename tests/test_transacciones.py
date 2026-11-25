"""Pruebas del módulo 2: recorridos de la Guía 7 y detección de patrones."""

import json

import pytest

from src import analisis_transacciones as at
from src import enrutamiento_financiero as ef
from src import gestion_red as gr
from src.algoritmos.recorridos import (bfs, bfs_niveles, ciclos_simples, dfs, es_bipartito,
                                       kosaraju, orden_topologico, tarjan)
from src.graph import Grafo
from src.utils import ruta_datos


def dirigido(aristas):
    g = Grafo(dirigido=True, ponderado=False)
    for u, v in aristas:
        for n in (u, v):
            if n not in g:
                g.agregar_nodo(n)
        g.agregar_arista(u, v)
    return g


def test_bfs_y_dfs_ejemplo_guia_7():
    g = dirigido([("A", "B"), ("A", "C"), ("B", "D"), ("C", "E")])
    assert bfs(g, "A") == ["A", "B", "C", "D", "E"]
    assert dfs(g, "A") == ["A", "B", "D", "C", "E"]
    assert bfs_niveles(g, ["A"]) == {"A": 0, "B": 1, "C": 1, "D": 2, "E": 2}


def test_orden_topologico_y_ciclo():
    g = dirigido([("A", "C"), ("B", "C"), ("C", "D")])
    orden = orden_topologico(g)
    assert orden.index("A") < orden.index("C") < orden.index("D")
    with pytest.raises(ValueError):
        orden_topologico(dirigido([("A", "B"), ("B", "A")]))


def test_kosaraju_y_tarjan_coinciden():
    g = dirigido([("1", "2"), ("2", "3"), ("3", "1"), ("3", "4"), ("4", "5"), ("5", "4"),
                  ("5", "6")])
    k = {frozenset(c) for c in kosaraju(g)}
    t = {frozenset(c) for c in tarjan(g)}
    assert k == t == {frozenset({"1", "2", "3"}), frozenset({"4", "5"}), frozenset({"6"})}


def test_ciclos_simples():
    g = dirigido([("A", "B"), ("B", "C"), ("C", "A"), ("A", "C")])
    ciclos = ciclos_simples(g, ["A", "B", "C"])
    assert sorted(len(c) for c in ciclos) == [3, 4]


def test_biparticion():
    g = Grafo(dirigido=False, ponderado=False)
    for n in "1234":
        g.agregar_nodo(n)
    for u, v in [("1", "2"), ("2", "3"), ("3", "4")]:
        g.agregar_arista(u, v)
    assert es_bipartito(g)[0]
    g.agregar_arista("1", "3")
    assert not es_bipartito(g)[0]


@pytest.fixture(scope="module")
def analisis():
    tit = gr.cargar_titularidad()
    cuentas = [n for n, a in tit.nodos.items() if a["tipo"] == "cuenta"]
    tiempos = ef.matriz_tiempos(gr.cargar_red_fisica())
    return at.analizar(at.cargar_transacciones(), at.cargar_retiros(), tiempos, cuentas)


@pytest.fixture(scope="module")
def esperado():
    with open(ruta_datos("patrones_esperados.json"), encoding="utf-8") as f:
        return json.load(f)


def test_pitufeo(analisis, esperado):
    alertas = analisis["pitufeo"]
    assert [a["cuenta_destino"] for a in alertas] == [esperado["pitufeo"]["destino"]]
    assert alertas[0]["emisores"] == esperado["pitufeo"]["origenes"]


def test_ciclo_de_fondos(analisis, esperado):
    grupos = analisis["grupos"]
    assert [g["cuentas"] for g in grupos] == [sorted(esperado["ciclo"])]
    assert len(grupos[0]["ciclos"]) == 1


def test_cuenta_puente(analisis, esperado):
    assert [a["cuenta_puente"] for a in analisis["puente"]] == [esperado["cuenta_puente"]]


def test_estratificacion(analisis):
    (hallazgo,) = analisis["estratificacion"]
    assert hallazgo["final"] == ["LY_FINAL"] and hallazgo["numero_capas"] == 3
    assert hallazgo["capas"][1] == ["LY_C1A", "LY_C1B", "LY_C1C"]
    assert hallazgo["origenes"] == ["LY_ORIG"]


def test_viaje_imposible_sin_falsos_positivos(analisis, esperado):
    tarjetas = sorted(a["tarjeta"] for a in analisis["viaje_imposible"])
    assert tarjetas == esperado["viaje_imposible"]
    assert "T0250" not in tarjetas


def test_proximidad(analisis):
    assert "S01" in analisis["proximidad"][1]  # emisor del pitufeo a un salto


def test_rastreo_de_fondos():
    grafo = at.construir_grafo(at.cargar_transacciones())
    caminos, intermediarios, receptores = at.rastrear(grafo, "LY_ORIG", 6, 10000)
    assert receptores == ["LY_FINAL"]
    assert set(intermediarios) == {"LY_C1A", "LY_C1B", "LY_C1C", "LY_C2A", "LY_C2B"}


def test_transaccion_con_cuenta_desconocida():
    eventos = [{"id": "X", "origen": "NO_EXISTE", "destino": "P0001", "monto": 10,
                "fecha_hora": "2026-06-01 10:00"}]
    with pytest.raises(Exception):
        at.construir_grafo(eventos, ["P0001"])
