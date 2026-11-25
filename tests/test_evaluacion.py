"""Pruebas del módulo 5: comparaciones, reproducibilidad y validación."""

from src import evaluacion_resultados as ev


def test_generador_reproducible():
    a = ev.grafo_aleatorio(50, 200, semilla=7)
    b = ev.grafo_aleatorio(50, 200, semilla=7)
    assert a.aristas() == b.aristas()
    assert a.numero_aristas() == 200


def test_comparaciones_coinciden():
    filas = (ev.comparar_rutas([60]) + ev.comparar_todos_pares([30]) + ev.comparar_cfc([80])
             + ev.comparar_mst([80]) + ev.comparar_flujo([40]))
    assert len(filas) == 10
    assert all(f["coincide"] for f in filas)
    assert all(f["tiempo_ms"] >= 0 and f["memoria_kb"] >= 0 for f in filas)


def test_todos_los_escenarios_validan():
    casos = ev.validar_escenarios()
    fallas = [c["caso"] for c in casos if not c["ok"]]
    assert fallas == []


def test_escenario_huaico():
    h = ev.escenario_huaico()
    antes, despues = h["tiempo_cusco_quillabamba"]
    assert despues > antes
    assert h["pendiente"][1] > h["pendiente"][0]
    assert {"HID", "STE"} <= set(h["nuevos_criticos"])
