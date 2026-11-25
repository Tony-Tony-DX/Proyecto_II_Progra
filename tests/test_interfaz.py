"""Pruebas de la interfaz gráfica: API JSON, animaciones y servidor local."""

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from src.interfaz import api
from src.interfaz.servidor import Manejador


def es_json(objeto):
    return json.loads(json.dumps(api.limpiar(objeto), allow_nan=False))


def test_respuestas_son_json_valido():
    for funcion in (api.resumen, api.red_fisica, api.fraude, api.titularidad, api.comparar_cfc,
                    api.huaico, api.validacion, lambda: api.red_enrutamiento("ruleteo"),
                    lambda: api.matriz_tiempos("johnson"), lambda: api.troncal("prim"),
                    lambda: api.proximidad("E_ORO01", 2), lambda: api.rastreo("LY_ORIG", 10000)):
        assert es_json(funcion())


def test_consulta_y_liquidez():
    r = es_json(api.consulta_ruta("CTA_CMA_QUI", "CTA_BX_LIMA", 5000))
    assert r["costo"]["costo"] == 3.5 and r["ruleteo"] is None
    plan = es_json(api.liquidez("alta", "costo_minimo", [["OLL", "SMA"]]))
    assert plan["cerrados"] == [["OLL", "SMA"]] and plan["pendientes"]


@pytest.mark.parametrize("algoritmo", ["bfs", "dijkstra", "kruskal", "edmonds_karp", "floyd"])
@pytest.mark.parametrize("red", ["guia", "cusco"])
def test_animaciones(algoritmo, red):
    d = es_json(api.animacion(algoritmo, red))
    assert d["pasos"], "la animación debe tener pasos"
    if algoritmo == "kruskal" and red == "guia":
        assert d["resultado"]["costo"] == 10
    if algoritmo == "edmonds_karp" and red == "guia":
        assert d["resultado"]["flujo_maximo"] == 23


def test_edicion_de_la_red_y_restablecer():
    api.restablecer()
    datos = api.editar_arista("eliminar", "OLL", "MPP", {})
    assert len(datos["aristas"]) == 39
    with pytest.raises(Exception):
        api.editar_arista("agregar", "CUS_BC", "URC", {"riesgo": 3})  # duplicada
    assert len(api.restablecer()["aristas"]) == 40


def test_cargar_archivo_txt():
    d = api.cargar_archivo("red.txt", "A B 2\nB C 3\n", True)
    assert len(d["nodos"]) == 3 and d["componentes"] == 1


def test_servidor_responde():
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    base = f"http://127.0.0.1:{servidor.server_address[1]}"
    try:
        with urllib.request.urlopen(base + "/") as r:
            assert b"Caja Municipal Andina" in r.read()
        with urllib.request.urlopen(base + "/api/red") as r:
            assert len(json.loads(r.read())["nodos"]) == 39
        peticion = urllib.request.Request(base + "/api/consulta", method="POST",
                                          data=json.dumps({"origen": "TC_EXT", "destino": "CTA_REST_MPP",
                                                           "monto": 300}).encode(),
                                          headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(peticion) as r:
            assert json.loads(r.read())["costo"]["costo"] == 10.5
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(base + "/api/proximidad?cuenta=NO_EXISTE")
        assert error.value.code == 400
    finally:
        servidor.shutdown()
        servidor.server_close()
