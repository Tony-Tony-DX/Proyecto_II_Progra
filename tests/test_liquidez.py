"""Pruebas del módulo 4: flujo máximo (Guía 11), MST (Guía 8) y escenarios."""

import pytest

from src import distribucion_liquidez as dl
from src import gestion_red as gr
from src.algoritmos.arbol_expansion import kruskal, prim
from src.algoritmos.flujo import (RedFlujo, corte_minimo, edmonds_karp, ford_fulkerson,
                                  ford_fulkerson_costo_minimo, verificar_flujo)
from src.graph import Grafo


def red_clasica():
    """Red de flujo clásica (Cormen et al.) con flujo máximo 23."""
    red = RedFlujo()
    for u, v, c in [("s", "v1", 16), ("s", "v2", 13), ("v1", "v3", 12), ("v2", "v1", 4),
                    ("v2", "v4", 14), ("v3", "v2", 9), ("v3", "t", 20), ("v4", "v3", 7),
                    ("v4", "t", 4)]:
        red.agregar_arco(u, v, c)
    return red


@pytest.mark.parametrize("algoritmo", [ford_fulkerson, edmonds_karp])
def test_flujo_maximo_red_clasica(algoritmo):
    red = red_clasica()
    valor, _ = algoritmo(red, "s", "t")
    assert valor == 23
    assert verificar_flujo(red, "s", "t") == []


def test_teorema_flujo_maximo_corte_minimo():
    red = red_clasica()
    valor, _ = edmonds_karp(red, "s", "t")
    S, corte, capacidad = corte_minimo(red, "s")
    assert capacidad == valor and "s" in S and "t" not in S


def test_costo_minimo_elige_ruta_barata():
    red = RedFlujo()
    red.agregar_arco("s", "a", 10, costo=1)
    red.agregar_arco("a", "t", 10, costo=1)
    red.agregar_arco("s", "b", 10, costo=5)
    red.agregar_arco("b", "t", 10, costo=5)
    red.agregar_arco("x", "t", 0)
    valor, costo, _ = ford_fulkerson_costo_minimo(red, "s", "t")
    assert valor == 20 and costo == 10 * 2 + 10 * 10
    red2 = RedFlujo()
    red2.agregar_arco("s", "t", 5, costo=1)
    red2.agregar_arco("s", "m", 5, costo=1)
    red2.agregar_arco("m", "t", 5, costo=1)
    _, costo2, _ = ford_fulkerson_costo_minimo(red2, "s", "t")
    assert costo2 == 5 * 1 + 5 * 2


def test_kruskal_y_prim_mismo_costo():
    g = Grafo(dirigido=False, ponderado=True)
    for n in ["R1", "R2", "R3", "R4", "R5"]:
        g.agregar_nodo(n)
    # Ejercicio resuelto 2 de la Guía 8 (red hidráulica): costo mínimo 10
    for u, v, w in [("R1", "R2", 4), ("R1", "R3", 2), ("R3", "R2", 1), ("R3", "R4", 8),
                    ("R3", "R5", 10), ("R2", "R4", 5), ("R4", "R5", 2)]:
        g.agregar_arista(u, v, peso=w)
    (a1, c1), (a2, c2) = kruskal(g), prim(g, inicio="R1")
    assert c1 == c2 == 10 and len(a1) == len(a2) == 4


def test_division_de_nodos_respeta_almacenamiento():
    liq = gr.cargar_red_liquidez()
    plan = dl.planificar(liq, "alta")
    for a in plan["almacenes"]:
        assert a["uso"] <= a["capacidad"]


@pytest.fixture(scope="module")
def planes():
    liq = gr.cargar_red_liquidez()
    return {
        "normal": dl.planificar(liq, "normal"),
        "alta": dl.planificar(liq, "alta"),
        "alta_ek": dl.planificar(liq, "alta", "edmonds_karp"),
        "huaico": dl.planificar(gr.cargar_red_liquidez([("OLL", "SMA")]), "alta"),
    }


def test_temporada_normal_cubierta(planes):
    p = planes["normal"]
    assert p["flujo_maximo"] == p["demanda_total"] and not p["pendientes"]


def test_temporada_alta_cuello_de_botella_tren(planes):
    p = planes["alta"]
    rutas_corte = {c[1].split(" (")[0] for c in p["corte"] if c[0] == "ruta"}
    assert rutas_corte == {"OLL -> MPP", "HID -> MPP"}
    assert p["verificacion"] == []
    assert sum(d["pendiente"] for d in p["pendientes"]) == 400


def test_costo_minimo_vs_edmonds_karp(planes):
    assert planes["alta"]["flujo_maximo"] == planes["alta_ek"]["flujo_maximo"]
    assert planes["alta"]["costo_total"] <= planes["alta_ek"]["costo_total"]


def test_huaico_afecta_la_convencion(planes):
    pendientes = {d["nodo"] for d in planes["huaico"]["pendientes"]}
    assert {"QUI_AG", "ECH"} <= pendientes
    assert planes["huaico"]["flujo_maximo"] < planes["alta"]["flujo_maximo"]


def test_red_troncal_excluye_abra_malaga():
    troncal = dl.red_troncal(gr.cargar_red_fisica(), "riesgo")
    fuera = {frozenset((u, v)) for u, v, _ in troncal["fuera"]}
    assert frozenset(("OLL", "SMA")) in fuera
    assert len(troncal["aristas"]) == 38  # V - 1


def test_puntos_criticos():
    criticos = dl.nodos_criticos(gr.cargar_red_fisica())
    assert {"OLL", "URC", "URU_BR", "SMA", "CUS_BC", "OCO", "SIC_BR"} <= set(criticos)
    assert "QUI_BR" in criticos["SMA"]
    assert "MPP" in criticos["OLL"] and "ATM_MPP" in criticos["OLL"]
    assert "CAL" not in criticos  # Calca está en un ciclo (Cusco - Pisac - Calca - Urubamba)
