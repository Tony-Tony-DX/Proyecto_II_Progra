"""Capa de servicios de la interfaz gráfica.

Cada función recibe parámetros simples y devuelve diccionarios listos para
convertirse en JSON. Aquí no hay algoritmos nuevos: solo se llaman los módulos
1 a 5 y se preparan los datos para dibujarlos.
"""

import math
import os
import tempfile
import time

from src import analisis_transacciones as at
from src import distribucion_liquidez as dl
from src import enrutamiento_financiero as ef
from src import evaluacion_resultados as ev
from src import gestion_red as gr
from src.algoritmos.arbol_expansion import kruskal
from src.algoritmos.flujo import RedFlujo, edmonds_karp
from src.algoritmos.recorridos import (bfs, componentes_conexas, kosaraju, puntos_criticos,
                                       tarjan)
from src.algoritmos.rutas_cortas import (camino_floyd, dijkstra, floyd_warshall,
                                         reconstruir_camino)
from src.graph import Grafo
from src.utils import REPORTES_DIR, medir

# ----------------------------------------------------------------- estado
_estado = {"fisica": None, "analisis": None}


def _fisica():
    if _estado["fisica"] is None:
        _estado["fisica"] = gr.cargar_red_fisica()
    return _estado["fisica"]


def _analisis():
    if _estado["analisis"] is None:
        tit = gr.cargar_titularidad()
        cuentas = [n for n, a in tit.nodos.items() if a["tipo"] == "cuenta"]
        tiempos = ef.matriz_tiempos(gr.cargar_red_fisica())
        _estado["analisis"] = at.analizar(at.cargar_transacciones(), at.cargar_retiros(),
                                          tiempos, cuentas)
    return _estado["analisis"]


def limpiar(valor):
    """Convierte inf/nan en None y tuplas/conjuntos en listas (JSON válido)."""
    if isinstance(valor, float) and (math.isinf(valor) or math.isnan(valor)):
        return None
    if isinstance(valor, dict):
        return {str(k): limpiar(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple, set, frozenset)):
        return [limpiar(v) for v in valor]
    return valor


def grafo_a_json(grafo):
    return {
        "dirigido": grafo.dirigido,
        "ponderado": grafo.ponderado,
        "nodos": [{"id": n, **a} for n, a in grafo.nodos.items()],
        "aristas": [{"u": u, "v": v, **a} for u, v, a in grafo.aristas()],
    }


# ------------------------------------------------------------------ inicio
def resumen():
    res = _analisis()
    fisica = gr.cargar_red_fisica()
    liq = gr.cargar_red_liquidez()
    enr = gr.cargar_red_enrutamiento()
    tit = gr.cargar_titularidad()
    planes = {
        "normal": dl.planificar(liq, "normal"),
        "alta": dl.planificar(liq, "alta"),
        "huaico": dl.planificar(gr.cargar_red_liquidez([("OLL", "SMA")]), "alta"),
    }
    casos = ev.validar_escenarios()
    return {
        "redes": [
            {"nombre": "Red física (carreteras y tren)", "V": fisica.numero_nodos(),
             "E": fisica.numero_aristas(), "tipo": "no dirigida · ponderada"},
            {"nombre": "Red de liquidez", "V": liq.numero_nodos(), "E": liq.numero_aristas(),
             "tipo": "dirigida · ponderada"},
            {"nombre": "Canales de operación", "V": enr.numero_nodos(),
             "E": enr.numero_aristas(), "tipo": "dirigida · ponderada"},
            {"nombre": "Transacciones entre cuentas", "V": res["grafo"].numero_nodos(),
             "E": res["grafo"].numero_aristas(), "tipo": "dirigida · ponderada"},
            {"nombre": "Titularidad cliente – cuenta", "V": tit.numero_nodos(),
             "E": tit.numero_aristas(), "tipo": "no dirigida · no ponderada"},
        ],
        "transacciones": len(at.cargar_transacciones()),
        "alertas": {
            "Pitufeo": len(res["pitufeo"]), "Ciclos de fondos": len(res["grupos"]),
            "Cuentas puente": len(res["puente"]), "Estratificación": len(res["estratificacion"]),
            "Viaje imposible": len(res["viaje_imposible"]),
        },
        "cobertura": {k: p["cobertura_pct"] for k, p in planes.items()},
        "pendiente": {k: sum(d["pendiente"] for d in p["pendientes"]) for k, p in planes.items()},
        "validacion": {"ok": sum(c["ok"] for c in casos), "total": len(casos)},
    }


# --------------------------------------------------------------- módulo 1
def red_fisica():
    g = _fisica()
    datos = grafo_a_json(g)
    datos["problemas"] = g.validar()
    comps = componentes_conexas(g)
    datos["componentes"] = sorted((sorted(c) for c in comps), key=len, reverse=True)
    datos["criticos"] = puntos_criticos(g)
    tipos = {}
    for a in g.nodos.values():
        tipos[a.get("tipo", "sin tipo")] = tipos.get(a.get("tipo", "sin tipo"), 0) + 1
    datos["tipos"] = tipos
    return datos


def editar_nodo(accion, nodo, atributos):
    g = _fisica()
    if accion == "agregar":
        g.agregar_nodo(nodo, **atributos)
    elif accion == "modificar":
        g.modificar_nodo(nodo, **atributos)
    elif accion == "eliminar":
        g.eliminar_nodo(nodo)
    else:
        raise ValueError("Acción no válida.")
    return red_fisica()


def editar_arista(accion, u, v, atributos):
    g = _fisica()
    if accion == "agregar":
        g.agregar_arista(u, v, **atributos)
    elif accion == "modificar":
        g.modificar_arista(u, v, **atributos)
    elif accion == "eliminar":
        g.eliminar_arista(u, v)
    else:
        raise ValueError("Acción no válida.")
    return red_fisica()


def restablecer():
    _estado["fisica"] = gr.cargar_red_fisica()
    return red_fisica()


def cargar_archivo(nombre, contenido, dirigido=True):
    """Carga una red externa enviada desde el navegador (CSV de aristas, TXT o JSON)."""
    extension = os.path.splitext(nombre)[1].lower() or ".csv"
    with tempfile.NamedTemporaryFile("w", suffix=extension, delete=False,
                                     encoding="utf-8") as f:
        f.write(contenido)
        ruta = f.name
    try:
        if extension == ".json":
            g = gr.cargar_json(ruta)
        elif extension == ".txt":
            g = gr.cargar_txt(ruta, dirigido)
        else:
            g = Grafo(dirigido, True, nombre)
            gr.cargar_aristas_csv(g, ruta, crear_nodos=True)
    finally:
        os.unlink(ruta)
    g.nombre = nombre
    datos = grafo_a_json(g)
    datos["resumen"] = gr.resumen(g)
    datos["componentes"] = len(componentes_conexas(g))
    return datos


def titularidad():
    tit = gr.cargar_titularidad()
    problemas = gr.validar_titularidad(tit)
    clientes = [n for n, a in tit.nodos.items() if a["tipo"] == "cliente"]
    multiples = [{"cliente": c, "cuentas": sorted(v for v, _ in tit.vecinos(c))}
                 for c in clientes if tit.grado_salida(c) > 1]
    return {"clientes": len(clientes), "cuentas": tit.numero_nodos() - len(clientes),
            "bipartito": not problemas, "problemas": problemas, "multiples": multiples}


# --------------------------------------------------------------- módulo 2
def _subgrafo(grafo, nodos, capas=None):
    conjunto = set(nodos)
    aristas = [{"u": u, "v": v, "monto": a.get("monto_total"), "n": a.get("n_operaciones")}
               for u in conjunto for v, a in grafo.vecinos(u) if v in conjunto]
    return {"nodos": [{"id": n, "capa": (capas or {}).get(n, 0)} for n in nodos],
            "aristas": aristas}


def fraude():
    res = _analisis()
    g = res["grafo"]
    fisica = gr.cargar_red_fisica()
    orden, dist, sig = floyd_warshall(fisica, "tiempo_h")

    pitufeo = []
    for a in res["pitufeo"]:
        capas = {e: 0 for e in a["emisores"]}
        capas[a["cuenta_destino"]] = 1
        pitufeo.append({**a, "grafo": _subgrafo(g, list(capas), capas)})
    ciclos = []
    for grupo in res["grupos"]:
        ciclos.append({**grupo, "grafo": _subgrafo(g, grupo["cuentas"])})
    puentes = []
    for a in res["puente"]:
        capas = {a["de"]: 0, a["cuenta_puente"]: 1, **{r: 2 for r in a["receptores"]}}
        puentes.append({**a, "grafo": _subgrafo(g, list(capas), capas)})
    capas_alertas = []
    for h in res["estratificacion"]:
        capas = {c: int(k) for k, cuentas in h["capas"].items() for c in cuentas}
        capas_alertas.append({**h, "grafo": _subgrafo(g, list(capas), capas)})
    viajes = []
    for a in res["viaje_imposible"]:
        viajes.append({**a, "camino": camino_floyd(orden, sig, a["cajero_1"], a["cajero_2"])})
    return limpiar({
        "cuentas": g.numero_nodos(), "relaciones": g.numero_aristas(),
        "pitufeo": pitufeo, "ciclos": ciclos, "puentes": puentes,
        "estratificacion": capas_alertas, "viajes": viajes,
        "marcadas": res["marcadas"],
        "proximidad": {str(k): len(v) for k, v in res["proximidad"].items()},
        "umbral": at.UMBRAL_MONTO, "umbral_alto": at.UMBRAL_ALTO_VALOR, "aviso": at.AVISO,
    })


def proximidad(cuenta, niveles=2, maximo_por_nivel=24):
    g = _analisis()["grafo"]
    if cuenta not in g:
        raise ValueError(f"La cuenta '{cuenta}' no existe.")
    por_nivel = at.proximidad(g, [cuenta], niveles)
    capas = {cuenta: 0}
    totales = {}
    for nivel, cuentas in por_nivel.items():
        totales[nivel] = len(cuentas)
        for c in cuentas[:maximo_por_nivel]:
            capas[c] = nivel
    sub = _subgrafo(g, list(capas), capas)
    return limpiar({"cuenta": cuenta, "totales": totales, "grafo": sub})


def rastreo(cuenta, minimo=0):
    g = _analisis()["grafo"]
    if cuenta not in g:
        raise ValueError(f"La cuenta '{cuenta}' no existe.")
    caminos, intermediarios, receptores = at.rastrear(g, cuenta, 6, minimo)
    caminos = caminos[:60]
    profundidad = {}
    for c in caminos:
        for i, n in enumerate(c):
            profundidad[n] = max(profundidad.get(n, 0), i)
    nodos = list(profundidad) or [cuenta]
    return limpiar({"caminos": caminos, "intermediarios": intermediarios,
                    "receptores": receptores,
                    "grafo": _subgrafo(g, nodos, profundidad or {cuenta: 0})})


def comparar_cfc():
    g = _analisis()["grafo"]
    c1, t1, k1 = medir(kosaraju, g)
    c2, t2, k2 = medir(tarjan, g)
    return {"kosaraju": {"componentes": len(c1), "ms": round(t1 * 1000, 2), "kb": round(k1, 1)},
            "tarjan": {"componentes": len(c2), "ms": round(t2 * 1000, 2), "kb": round(k2, 1)},
            "coinciden": {frozenset(c) for c in c1} == {frozenset(c) for c in c2},
            "grupos": [sorted(c) for c in c2 if len(c) > 1]}


def cuentas():
    return sorted(_analisis()["grafo"].nodos)


# --------------------------------------------------------------- módulo 3
def red_enrutamiento(variante=None):
    g = gr.cargar_red_enrutamiento(variante or None)
    datos = grafo_a_json(g)
    datos["escenarios"] = [{"titulo": t, "origen": o, "destino": d, "monto": m}
                           for t, o, d, m in ef.ESCENARIOS]
    return limpiar(datos)


def consulta_ruta(origen, destino, monto, variante=None):
    g = gr.cargar_red_enrutamiento(variante or None)
    costo = ef.mejor_ruta(g, origen, destino, monto, "costo")
    tiempo = ef.mejor_ruta(g, origen, destino, monto, "tiempo")
    viables, no_viables = ef.rutas_alternativas(g, origen, destino, monto)
    ruleteo = ef.detectar_ruleteo(g, monto)
    return limpiar({"costo": costo, "tiempo": tiempo, "viables": viables,
                    "no_viables": no_viables, "ruleteo": ruleteo})


def matriz_tiempos(algoritmo="floyd"):
    fisica = gr.cargar_red_fisica()
    inicio = time.perf_counter()
    tiempos = ef.matriz_tiempos(fisica, algoritmo)
    ms = (time.perf_counter() - inicio) * 1000
    puntos = ["CUS_BC", "URU_BR", "OLL", "MPP", "QUI_BR", "URC", "OCO", "QCM", "SIC_BR", "YAU"]
    return limpiar({"puntos": puntos,
                    "nombres": [fisica.nodos[p]["nombre"] for p in puntos],
                    "matriz": [[round(tiempos[u][v], 2) for v in puntos] for u in puntos],
                    "ms": round(ms, 2), "algoritmo": algoritmo})


# --------------------------------------------------------------- módulo 4
def liquidez(temporada="alta", metodo="costo_minimo", cerrados=None, umbral_riesgo=None):
    cerrados = [tuple(p) for p in cerrados or []]
    grafo = gr.cargar_red_liquidez(cerrados)
    inicio = time.perf_counter()
    plan = dl.planificar(grafo, temporada, metodo, umbral_riesgo)
    ms = (time.perf_counter() - inicio) * 1000
    # flujo combinado por tramo físico (los dos sentidos de una carretera)
    tramos = {}
    for r in plan["rutas"]:
        clave = tuple(sorted((r["origen"], r["destino"])))
        t = tramos.setdefault(clave, {"u": clave[0], "v": clave[1], "flujo": 0,
                                      "capacidad": r["capacidad"], "uso_pct": 0,
                                      "desde": r["origen"], "hacia": r["destino"], "max": -1})
        t["flujo"] += r["flujo"]
        t["uso_pct"] = max(t["uso_pct"], r["uso_pct"])
        if r["flujo"] > t["max"]:
            t["max"], t["desde"], t["hacia"] = r["flujo"], r["origen"], r["destino"]
    fisica = gr.cargar_red_fisica()
    plan.pop("red")
    return limpiar({
        **plan, "ms": round(ms, 2), "tramos": list(tramos.values()),
        "nodos": [{"id": n, **a} for n, a in fisica.nodos.items()],
        "fisicas": [{"u": u, "v": v, **a} for u, v, a in fisica.aristas()],
        "cerrados": cerrados,
    })


def troncal(algoritmo="kruskal", cerrados=None):
    fisica = gr.cargar_red_fisica([tuple(p) for p in cerrados or []])
    t = dl.red_troncal(fisica, "riesgo", algoritmo)
    return limpiar({"aristas": [{"u": u, "v": v, "riesgo": p} for u, v, p in t["aristas"]],
                    "fuera": [{"u": u, "v": v, "riesgo": p} for u, v, p in t["fuera"]],
                    "costo": t["costo"], "criticos": puntos_criticos(fisica),
                    "componentes": len(componentes_conexas(fisica))})


# --------------------------------------------------------------- módulo 5
def validacion():
    return limpiar({"casos": ev.validar_escenarios()})


def comparacion(modo="rapido"):
    return limpiar({"filas": ev.ejecutar_comparaciones(modo)})


def huaico():
    return limpiar(ev.escenario_huaico())


# --------------------------------------------------------------- animaciones
GUIAS = {
    "bfs": {
        "titulo": "Guía 7 – grafo dirigido de ejemplo",
        "nodos": {"A": (2, 0), "B": (1, 1), "C": (3, 1), "D": (0.4, 2), "E": (1.6, 2),
                  "F": (3, 2), "G": (2.2, 3)},
        "aristas": [("A", "B", 1), ("A", "C", 1), ("B", "D", 1), ("B", "E", 1), ("C", "F", 1),
                    ("E", "G", 1), ("F", "G", 1)],
        "dirigido": True,
    },
    "dijkstra": {
        "titulo": "Guía 9 – Figura 1 (grafo dirigido ponderado)",
        "nodos": {"A": (0, 0), "B": (1.6, 0), "E": (3.2, 0.6), "C": (0, 1.6), "D": (1.6, 1.6)},
        "aristas": [("A", "B", 4), ("A", "C", 2), ("C", "D", 1), ("D", "B", 3), ("B", "E", 5),
                    ("D", "E", 2)],
        "dirigido": True,
    },
    "kruskal": {
        "titulo": "Guía 8 – red hidráulica (ejercicio resuelto 2)",
        "nodos": {"R1": (0, 1), "R2": (1.5, 0), "R3": (1.5, 2), "R4": (3, 0.4), "R5": (3, 2)},
        "aristas": [("R1", "R2", 4), ("R1", "R3", 2), ("R3", "R2", 1), ("R3", "R4", 8),
                    ("R3", "R5", 10), ("R2", "R4", 5), ("R4", "R5", 2)],
        "dirigido": False,
    },
    "edmonds_karp": {
        "titulo": "Red de flujo clásica (Cormen et al.)",
        "nodos": {"s": (0, 1), "v1": (1, 0), "v2": (1, 2), "v3": (2, 0), "v4": (2, 2), "t": (3, 1)},
        "aristas": [("s", "v1", 16), ("s", "v2", 13), ("v1", "v3", 12), ("v2", "v1", 4),
                    ("v2", "v4", 14), ("v3", "v2", 9), ("v3", "t", 20), ("v4", "v3", 7),
                    ("v4", "t", 4)],
        "dirigido": True,
    },
    "floyd": {
        "titulo": "Guía 10 – red de billeteras e interoperabilidad",
        "nodos": {"A": (0, 0), "B": (2, 0), "X": (3.4, 0), "C": (0, 1.5), "D": (1.4, 1.5),
                  "E": (3.4, 1.5)},
        "aristas": [("A", "B", 4), ("A", "C", 2), ("B", "D", 5), ("C", "D", 1), ("D", "E", 3),
                    ("E", "X", 2), ("B", "X", 10), ("C", "E", 8)],
        "dirigido": True,
    },
}

DESCRIPCIONES = {
    "bfs": "BFS recorre la red por niveles con una cola FIFO: primero los vecinos directos, "
           "luego los vecinos de los vecinos. En el módulo 2 da la proximidad (en saltos) a "
           "una cuenta marcada.",
    "dijkstra": "Dijkstra extrae siempre el nodo con menor distancia conocida (cola de "
                "prioridad) y relaja sus aristas. Requiere pesos no negativos. En el módulo 3 "
                "elige la ruta de menor comisión o tiempo.",
    "kruskal": "Kruskal ordena las aristas de menor a mayor y acepta cada una si no forma "
               "ciclo (Union-Find). En el módulo 4 construye la red troncal de menor riesgo.",
    "edmonds_karp": "Edmonds-Karp busca con BFS el camino aumentante con menos arcos, envía "
                    "por él su cuello de botella y repite hasta que no haya caminos. En el "
                    "módulo 4 calcula cuánto efectivo puede distribuirse.",
    "floyd": "Floyd-Warshall prueba cada nodo k como intermediario: si ir de i a j pasando "
             "por k es más barato, actualiza la matriz. En el módulo 2 da los tiempos mínimos "
             "para detectar el viaje imposible.",
}


def _grafo_guia(clave):
    datos = GUIAS[clave]
    g = Grafo(datos["dirigido"], True, datos["titulo"])
    for n in datos["nodos"]:
        g.agregar_nodo(n)
    for u, v, w in datos["aristas"]:
        g.agregar_arista(u, v, peso=w)
    return g


def animacion(algoritmo, red="guia", origen=None):
    if algoritmo not in DESCRIPCIONES:
        raise ValueError("Algoritmo no disponible para animación.")
    traza = []
    resultado = {}
    if red == "cusco" and algoritmo != "floyd":
        if algoritmo == "edmonds_karp":
            liq = gr.cargar_red_liquidez()
            red_flujo, _ = dl.construir_red_flujo(liq, "alta")
            valor, aumentos = edmonds_karp(red_flujo, dl.FUENTE, dl.SUMIDERO, traza)
            for paso in traza:
                paso["camino"] = [dl._base(n) for n in paso["camino"]
                                  if n not in (dl.FUENTE, dl.SUMIDERO)]
                limpio = []
                for n in paso["camino"]:
                    if not limpio or limpio[-1] != n:
                        limpio.append(n)
                paso["camino"] = limpio
            resultado = {"flujo_maximo": valor, "aumentos": aumentos}
        g = gr.cargar_red_fisica()
        atributo = {"bfs": None, "dijkstra": "tiempo_h", "kruskal": "riesgo",
                    "edmonds_karp": None}[algoritmo]
        origen = origen or "CUS_BC"
        layout = "mapa"
        titulo = "Red física de la Caja Municipal Andina (Cusco)"
    else:
        g = _grafo_guia(algoritmo)
        atributo = "peso"
        origen = origen or ("s" if algoritmo == "edmonds_karp" else "A")
        layout = "guia"
        titulo = GUIAS[algoritmo]["titulo"]

    if algoritmo == "bfs":
        bfs(g, origen, traza)
    elif algoritmo == "dijkstra":
        dist, ant = dijkstra(g, origen, atributo, traza)
        resultado = {"distancias": dist,
                     "caminos": {n: reconstruir_camino(ant, n) for n in g.nodos}}
    elif algoritmo == "kruskal":
        arbol, costo = kruskal(g, atributo, traza)
        resultado = {"costo": costo, "aristas": len(arbol)}
    elif algoritmo == "edmonds_karp" and red != "cusco":
        red_flujo = RedFlujo()
        for u, v, a in g.aristas():
            red_flujo.agregar_arco(u, v, a["peso"])
        valor, aumentos = edmonds_karp(red_flujo, "s", "t", traza)
        resultado = {"flujo_maximo": valor, "aumentos": aumentos}
    elif algoritmo == "floyd":
        orden, dist, _ = floyd_warshall(g, "peso", traza)
        resultado = {"orden": orden}

    nodos = []
    for n, a in g.nodos.items():
        item = {"id": n, **a}
        if layout == "guia":
            item["x"], item["y"] = GUIAS[algoritmo]["nodos"][n]
        nodos.append(item)
    aristas = [{"u": u, "v": v, "peso": (a.get(atributo) if atributo else None)}
               for u, v, a in g.aristas()]
    return limpiar({"algoritmo": algoritmo, "titulo": titulo, "layout": layout,
                    "dirigido": g.dirigido, "origen": origen, "nodos": nodos,
                    "aristas": aristas, "pasos": traza, "resultado": resultado,
                    "descripcion": DESCRIPCIONES[algoritmo]})


# ---------------------------------------------------------------- reportes
def listar_reportes():
    if not os.path.isdir(REPORTES_DIR):
        return []
    return sorted(f for f in os.listdir(REPORTES_DIR) if not f.startswith("."))


def generar_reportes():
    import builtins
    import contextlib
    import io

    import main

    original = builtins.input
    builtins.input = lambda *a, **k: ""
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            main.generar_todo()
    finally:
        builtins.input = original
    return listar_reportes()
