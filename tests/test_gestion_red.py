"""Pruebas del módulo 1: estructura común del grafo, carga y validación."""

import pytest

from src import gestion_red as gr
from src.graph import ErrorValidacion, Grafo


def red_pequena(dirigido=True):
    g = Grafo(dirigido=dirigido, ponderado=True)
    for n in "ABCD":
        g.agregar_nodo(n)
    g.agregar_arista("A", "B", comision=4.5)
    g.agregar_arista("A", "C", comision=2.0)
    g.agregar_arista("B", "D", comision=5.1)
    return g


def test_crear_modificar_eliminar():
    g = red_pequena()
    assert g.numero_nodos() == 4 and g.numero_aristas() == 3
    g.modificar_arista("A", "B", comision=1.0)
    assert g.atributos_arista("A", "B")["comision"] == 1.0
    g.eliminar_arista("A", "C")
    assert not g.existe_arista("A", "C")
    g.eliminar_nodo("B")
    assert "B" not in g and not g.existe_arista("A", "B")
    assert g.validar() == []


def test_lista_adyacencia_formato_de_la_guia():
    g = red_pequena()
    assert g.lista_adyacencia("comision")["A"] == [("B", 4.5), ("C", 2.0)]


@pytest.mark.parametrize("accion", [
    lambda g: g.agregar_arista("A", "Z", comision=1),     # nodo inexistente
    lambda g: g.agregar_arista("A", "B", comision=1),     # duplicada no justificada
    lambda g: g.agregar_arista("A", "A", comision=1),     # lazo
    lambda g: g.agregar_arista("C", "D", capacidad=-5),   # valor inválido
    lambda g: g.agregar_arista("C", "D", nombre="x"),     # ponderado sin peso numérico
    lambda g: g.agregar_nodo("A"),                        # nodo repetido
])
def test_validaciones_rechazan_datos_invalidos(accion):
    with pytest.raises(ErrorValidacion):
        accion(red_pequena())


def test_no_dirigido_es_simetrico_y_comparte_atributos():
    g = red_pequena(dirigido=False)
    assert g.existe_arista("B", "A")
    g.modificar_arista("B", "A", comision=9)
    assert g.atributos_arista("A", "B")["comision"] == 9
    assert g.numero_aristas() == 3


def test_no_ponderado_peso_unitario():
    g = Grafo(dirigido=False, ponderado=False)
    g.agregar_nodo("x")
    g.agregar_nodo("y")
    g.agregar_arista("x", "y")
    assert g.peso("x", "y") == 1


def test_txt_y_json(tmp_path):
    txt = tmp_path / "red.txt"
    txt.write_text("# comentario\nA B 3\nB C 4\n", encoding="utf-8")
    g = gr.cargar_txt(str(txt))
    assert g.ponderado and g.peso("B", "C", "peso") == 4
    destino = tmp_path / "red.json"
    gr.guardar_json(g, str(destino))
    g2 = gr.cargar_json(str(destino))
    assert g2.numero_aristas() == 2 and g2.peso("A", "B", "peso") == 3


def test_txt_invalido(tmp_path):
    txt = tmp_path / "malo.txt"
    txt.write_text("A B C D\n", encoding="utf-8")
    with pytest.raises(ErrorValidacion):
        gr.cargar_txt(str(txt))


def test_csv_rechaza_nodo_inexistente(tmp_path):
    csv = tmp_path / "aristas.csv"
    csv.write_text("origen,destino,comision\nA,Z,1\n", encoding="utf-8")
    g = red_pequena()
    with pytest.raises(ErrorValidacion):
        gr.cargar_aristas_csv(g, str(csv))


def test_redes_de_la_caja_cargan_sin_problemas():
    fisica = gr.cargar_red_fisica()
    assert fisica.numero_nodos() == 39 and fisica.validar() == []
    liquidez = gr.cargar_red_liquidez()
    # las rutas "doble" generan dos arcos
    assert liquidez.existe_arista("OLL", "MPP") and liquidez.existe_arista("MPP", "OLL")
    assert not liquidez.existe_arista("ATM_MPP", "MPP")  # ruta de "ida"
    enrutamiento = gr.cargar_red_enrutamiento()
    assert enrutamiento.dirigido and enrutamiento.validar() == []


def test_cierre_de_tramo():
    assert not gr.cargar_red_fisica([("OLL", "SMA")]).existe_arista("OLL", "SMA")


def test_titularidad_bipartita():
    tit = gr.cargar_titularidad()
    assert gr.validar_titularidad(tit) == []
    # un cliente con dos cuentas (relación 1 a N)
    assert tit.grado_salida("CLE_COM1") == 2


def test_titularidad_inconsistente_se_detecta():
    tit = gr.cargar_titularidad()
    tit.agregar_arista("P0001", "P0002")  # cuenta enlazada con cuenta
    assert gr.validar_titularidad(tit)
