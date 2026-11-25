"""Módulo 4 – Planificación y optimización de la distribución de liquidez.

Modelo de flujo (problemática, sección 5.4 c y d):
- SÚPER-FUENTE -> cada bóveda, con capacidad = efectivo disponible (oferta).
- Cada agencia, agente o cajero -> SÚPER-SUMIDERO, con capacidad = demanda.
- División de nodos en las bóvedas regionales: v::entrada -> v::salida con
  capacidad = almacenamiento máximo.
- Las rutas de doble sentido ya llegan como dos arcos con la misma capacidad
  (ver gestion_red.cargar_red_liquidez).

Algoritmos (Guías 7, 8, 9 y 11):
- Edmonds-Karp: efectivo máximo distribuible.
- Ford-Fulkerson con caminos de menor costo (Bellman-Ford): mismo máximo con el
  menor costo de traslado.
- Corte mínimo: rutas que limitan la distribución.
- Kruskal / Prim: red troncal de menor riesgo.
- Puntos críticos: eliminación de nodos + BFS.
"""

from src.algoritmos.arbol_expansion import kruskal, prim
from src.algoritmos.flujo import (RedFlujo, corte_minimo, edmonds_karp, ford_fulkerson,
                                  ford_fulkerson_costo_minimo, verificar_flujo)
from src.algoritmos.recorridos import puntos_criticos
from src.utils import escribir_csv, formatear_tabla, ruta_reporte

FUENTE = "SUPER_FUENTE"
SUMIDERO = "SUPER_SUMIDERO"


def _base(nombre):
    return nombre.split("::")[0]


def construir_red_flujo(grafo, temporada="alta", umbral_riesgo=None):
    """Transforma la red de liquidez en una red de flujo con súper-fuente,
    súper-sumidero y división de nodos. Devuelve (red, etiquetas) donde
    etiquetas[indice_arco] = (tipo, u, v)."""
    columna = f"demanda_{temporada}"
    red = RedFlujo()
    etiquetas = {}
    dividido = {n for n, a in grafo.nodos.items()
                if a.get("tipo") == "boveda_regional" and a.get("almacenamiento")}

    def entrada(n):
        return f"{n}::entrada" if n in dividido else n

    def salida(n):
        return f"{n}::salida" if n in dividido else n

    red.agregar_nodo(FUENTE)
    red.agregar_nodo(SUMIDERO)
    for n, a in grafo.nodos.items():
        red.agregar_nodo(entrada(n))
        red.agregar_nodo(salida(n))
        if n in dividido:
            i = red.agregar_arco(entrada(n), salida(n), int(a["almacenamiento"]))
            etiquetas[i] = ("almacenamiento", n, n)
        if a.get("oferta"):
            i = red.agregar_arco(FUENTE, entrada(n), int(a["oferta"]))
            etiquetas[i] = ("oferta", FUENTE, n)
        if a.get(columna):
            i = red.agregar_arco(salida(n), SUMIDERO, int(a[columna]))
            etiquetas[i] = ("demanda", n, SUMIDERO)
    for u, v, a in grafo.aristas():
        if umbral_riesgo is not None and a.get("riesgo", 0) > umbral_riesgo:
            continue
        i = red.agregar_arco(salida(u), entrada(v), int(a["capacidad"]),
                             a.get("costo_unitario", 0))
        etiquetas[i] = ("ruta", u, v)
    return red, etiquetas


def planificar(grafo, temporada="alta", metodo="costo_minimo", umbral_riesgo=None):
    """Calcula el plan de distribución. ``metodo``: "costo_minimo",
    "edmonds_karp" o "ford_fulkerson"."""
    red, etiquetas = construir_red_flujo(grafo, temporada, umbral_riesgo)
    if metodo == "costo_minimo":
        valor, costo, aumentos = ford_fulkerson_costo_minimo(red, FUENTE, SUMIDERO)
        algoritmo = "Ford-Fulkerson con caminos de menor costo (Bellman-Ford)"
    else:
        funcion = edmonds_karp if metodo == "edmonds_karp" else ford_fulkerson
        valor, aumentos = funcion(red, FUENTE, SUMIDERO)
        costo = None
        algoritmo = "Edmonds-Karp (BFS)" if metodo == "edmonds_karp" else "Ford-Fulkerson (DFS)"

    rutas, demandas, almacenes, ofertas = [], [], [], []
    costo_calculado = 0
    for i, u, v, cap, flujo, c in red.arcos_originales():
        tipo, a, b = etiquetas[i]
        costo_calculado += flujo * c
        if tipo == "ruta":
            rutas.append({"origen": a, "destino": b, "capacidad": cap, "flujo": flujo,
                          "uso_pct": round(100 * flujo / cap, 1) if cap else 0,
                          "costo": round(flujo * c, 2)})
        elif tipo == "demanda":
            demandas.append({"nodo": a, "demanda": cap, "recibido": flujo,
                             "pendiente": cap - flujo})
        elif tipo == "almacenamiento":
            almacenes.append({"boveda": a, "capacidad": cap, "uso": flujo})
        else:
            ofertas.append({"boveda": b, "oferta": cap, "enviado": flujo})

    _, corte, capacidad_corte = corte_minimo(red, FUENTE)
    cuellos = []
    for u, v, cap in corte:
        bu, bv = _base(u), _base(v)
        if u == FUENTE:
            cuellos.append(("oferta", f"Efectivo disponible en {bv}", cap))
        elif v == SUMIDERO:
            continue  # demanda totalmente cubierta: no es un cuello de botella
        elif bu == bv:
            cuellos.append(("almacenamiento", f"Capacidad de la bóveda {bu}", cap))
        else:
            nombre = grafo.nodos[bu].get("nombre", bu) + " -> " + grafo.nodos[bv].get("nombre", bv)
            cuellos.append(("ruta", f"{bu} -> {bv} ({nombre})", cap))

    demanda_total = sum(d["demanda"] for d in demandas)
    return {
        "temporada": temporada, "algoritmo": algoritmo, "aumentos": aumentos,
        "flujo_maximo": valor, "demanda_total": demanda_total,
        "cobertura_pct": round(100 * valor / demanda_total, 1) if demanda_total else 100.0,
        "costo_total": round(costo if costo is not None else costo_calculado, 2),
        "rutas": sorted(rutas, key=lambda r: -r["flujo"]),
        "saturadas": [r for r in rutas if r["capacidad"] and r["flujo"] == r["capacidad"]],
        "demandas": demandas, "pendientes": [d for d in demandas if d["pendiente"] > 0],
        "almacenes": almacenes, "ofertas": ofertas,
        "corte": cuellos, "capacidad_corte": capacidad_corte,
        "verificacion": verificar_flujo(red, FUENTE, SUMIDERO),
        "red": red,
    }


def red_troncal(grafo_fisico, atributo="riesgo", algoritmo="kruskal"):
    """Árbol de expansión mínima sobre la red vial con peso = riesgo: conjunto
    de tramos de menor riesgo total que mantiene conectados todos los puntos."""
    arbol, costo = (kruskal if algoritmo == "kruskal" else prim)(grafo_fisico, atributo)
    en_arbol = {frozenset((u, v)) for u, v, _ in arbol}
    fuera = [(u, v, a.get(atributo)) for u, v, a in grafo_fisico.aristas()
             if frozenset((u, v)) not in en_arbol]
    return {"aristas": arbol, "costo": costo, "fuera": fuera, "algoritmo": algoritmo}


def nodos_criticos(grafo_fisico):
    return puntos_criticos(grafo_fisico)


# ---------------------------------------------------------------- reportes
def reporte_plan(plan, grafo=None):
    L = []
    L.append(f"PLAN DE DISTRIBUCIÓN DE LIQUIDEZ – temporada {plan['temporada']}")
    L.append(f"Algoritmo: {plan['algoritmo']}  ({plan['aumentos']} caminos aumentantes)")
    L.append(f"Efectivo distribuido (flujo máximo): S/ {plan['flujo_maximo']:,} mil "
             f"de una demanda de S/ {plan['demanda_total']:,} mil "
             f"({plan['cobertura_pct']} % de cobertura)")
    L.append(f"Costo total de traslado: S/ {plan['costo_total']:,.2f} mil")
    L.append("Verificación de capacidad y conservación: "
             + ("correcta" if not plan["verificacion"] else "; ".join(plan["verificacion"])))

    L.append("\nDemanda no cubierta por punto de atención:")
    if plan["pendientes"]:
        L.append(formatear_tabla(
            [[d["nodo"], d["demanda"], d["recibido"], d["pendiente"]] for d in plan["pendientes"]],
            ["Punto", "Demanda", "Recibido", "Pendiente"]))
    else:
        L.append("  Ninguna: toda la demanda queda cubierta.")

    L.append("\nCuellos de botella (corte mínimo, capacidad total "
             f"S/ {plan['capacidad_corte']:,} mil):")
    for tipo, descripcion, cap in plan["corte"]:
        L.append(f"  [{tipo}] {descripcion}: capacidad {cap:,}")

    L.append("\nRutas saturadas (flujo = capacidad):")
    for r in plan["saturadas"]:
        L.append(f"  {r['origen']} -> {r['destino']}: {r['flujo']:,} / {r['capacidad']:,}")

    L.append("\nUso de la capacidad de almacenamiento de las bóvedas regionales:")
    for a in plan["almacenes"]:
        L.append(f"  {a['boveda']}: {a['uso']:,} / {a['capacidad']:,}")

    L.append("\nRutas con mayor flujo:")
    L.append(formatear_tabla(
        [[r["origen"], r["destino"], r["flujo"], r["capacidad"], f"{r['uso_pct']} %", r["costo"]]
         for r in plan["rutas"] if r["flujo"] > 0][:20],
        ["Origen", "Destino", "Flujo", "Capacidad", "Uso", "Costo"]))
    return "\n".join(L)


def reporte_red_troncal(troncal, criticos):
    L = [f"RED TRONCAL DE MENOR RIESGO ({troncal['algoritmo'].capitalize()}, peso = riesgo)"]
    L.append(f"Tramos seleccionados: {len(troncal['aristas'])}  |  riesgo total: {troncal['costo']}")
    for u, v, p in sorted(troncal["aristas"], key=lambda t: -t[2]):
        L.append(f"  {u} - {v} (riesgo {p})")
    L.append("Tramos que no forman parte de la red troncal (alternativos):")
    for u, v, p in troncal["fuera"]:
        L.append(f"  {u} - {v} (riesgo {p})")
    L.append("\nPUNTOS CRÍTICOS (eliminación de nodos + BFS):")
    for nodo, separados in sorted(criticos.items()):
        L.append(f"  {nodo}: si falla, quedan aislados {', '.join(separados)}")
    return "\n".join(L)


def exportar_plan(plan, nombre="plan_liquidez.csv"):
    ruta = ruta_reporte(nombre)
    escribir_csv(ruta, plan["rutas"], ["origen", "destino", "capacidad", "flujo", "uso_pct", "costo"])
    return ruta
