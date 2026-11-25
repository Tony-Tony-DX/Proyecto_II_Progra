"""Módulo 5 – Evaluación, comparación y validación de resultados.

1) Validación con resultados esperados conocidos (patrones insertados en los
   datos, rutas calculadas a mano, propiedades del flujo).
2) Comparación empírica de alternativas de las guías sobre redes sintéticas
   generadas con semilla fija:
      Dijkstra vs Bellman-Ford          (rutas desde un origen)
      Floyd-Warshall vs Johnson         (todos los pares)
      Kosaraju vs Tarjan                (componentes fuertemente conexas)
      Kruskal vs Prim                   (árbol de expansión mínima)
      Ford-Fulkerson (DFS) vs Edmonds-Karp (flujo máximo)
   Tiempo: time.perf_counter. Memoria pico: tracemalloc.
3) Escenario de contingencia: huaico en Abra Málaga (antes / después).
"""

import json
import math
import random

from src import analisis_transacciones as at
from src import distribucion_liquidez as dl
from src import enrutamiento_financiero as ef
from src import gestion_red as gr
from src.algoritmos.arbol_expansion import kruskal, prim
from src.algoritmos.flujo import RedFlujo, edmonds_karp, ford_fulkerson, verificar_flujo
from src.algoritmos.recorridos import kosaraju, tarjan
from src.algoritmos.rutas_cortas import bellman_ford, dijkstra, floyd_warshall, johnson
from src.graph import Grafo
from src.utils import escribir_csv, formatear_tabla, medir, ruta_datos, ruta_reporte

SEMILLA = 2026

COMPLEJIDAD = {
    "Dijkstra": "O((V+E) log V)", "Bellman-Ford": "O(V·E)",
    "Floyd-Warshall": "O(V^3)", "Johnson": "O(V·E + V(V+E) log V)",
    "Kosaraju": "O(V+E)", "Tarjan": "O(V+E)",
    "Kruskal": "O(E log E)", "Prim": "O(E log V)",
    "Ford-Fulkerson (DFS)": "O(E·|f*|)", "Edmonds-Karp": "O(V·E^2)",
}

TAMANOS_RAPIDO = {
    "rutas": [100, 250, 500, 1000],
    "todos_pares": [25, 50, 100, 150],
    "cfc": [100, 500, 1000, 2000],
    "mst": [100, 500, 1000, 2000],
    "flujo": [50, 100, 200, 400],
}
TAMANOS_COMPLETO = {
    "rutas": [100, 500, 1000, 2000],
    "todos_pares": [50, 100, 200, 300],
    "cfc": [100, 500, 1000, 2000],
    "mst": [100, 500, 1000, 2000],
    "flujo": [100, 250, 500, 1000],
}


# ------------------------------------------------------- redes sintéticas
def grafo_aleatorio(n, m, semilla=SEMILLA, dirigido=True, peso=(1, 20)):
    """Grafo aleatorio con n nodos y ~m aristas. Primero se crea un camino que
    recorre todos los nodos (garantiza conectividad) y luego aristas al azar."""
    rng = random.Random(semilla * 1000 + n)
    g = Grafo(dirigido=dirigido, ponderado=True, nombre=f"aleatorio_{n}")
    for i in range(n):
        g.agregar_nodo(f"N{i}")
    orden = list(range(n))
    rng.shuffle(orden)
    for a, b in zip(orden, orden[1:]):
        g.agregar_arista(f"N{a}", f"N{b}", peso=rng.randint(*peso), capacidad=rng.randint(1, 100))
    intentos = 0
    while g.numero_aristas() < m and intentos < m * 20:
        intentos += 1
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b and not g.existe_arista(f"N{a}", f"N{b}"):
            g.agregar_arista(f"N{a}", f"N{b}", peso=rng.randint(*peso),
                             capacidad=rng.randint(1, 100))
    return g


def red_flujo_aleatoria(n, m, semilla=SEMILLA):
    g = grafo_aleatorio(n, m, semilla)
    red = RedFlujo()
    for u, v, a in g.aristas():
        red.agregar_arco(u, v, a["capacidad"])
    return red, "N0", f"N{n - 1}"


# ---------------------------------------------------------- comparaciones
def _fila(comparacion, algoritmo, n, m, seg, kb, resultado, coincide):
    return {"comparacion": comparacion, "algoritmo": algoritmo, "V": n, "E": m,
            "complejidad": COMPLEJIDAD[algoritmo], "tiempo_ms": round(seg * 1000, 3),
            "memoria_kb": round(kb, 1), "resultado": resultado, "coincide": coincide}


def comparar_rutas(tamanos):
    filas = []
    for n in tamanos:
        g = grafo_aleatorio(n, 4 * n)
        (d1, _), t1, k1 = medir(dijkstra, g, "N0")
        (d2, _, _), t2, k2 = medir(bellman_ford, g, "N0")
        ok = all(math.isclose(d1[x], d2[x]) or d1[x] == d2[x] for x in d1)
        suma = round(sum(d for d in d1.values() if d != math.inf), 1)
        filas.append(_fila("Rutas desde un origen", "Dijkstra", n, g.numero_aristas(), t1, k1, suma, ok))
        filas.append(_fila("Rutas desde un origen", "Bellman-Ford", n, g.numero_aristas(), t2, k2, suma, ok))
    return filas


def comparar_todos_pares(tamanos):
    filas = []
    for n in tamanos:
        g = grafo_aleatorio(n, 4 * n)
        (orden, dist, _), t1, k1 = medir(floyd_warshall, g)
        dj, t2, k2 = medir(johnson, g)
        ok = all(dist[i][j] == dj[u][v] or math.isclose(dist[i][j], dj[u][v])
                 for i, u in enumerate(orden) for j, v in enumerate(orden))
        suma = round(sum(x for fila in dist for x in fila if x != math.inf), 1)
        filas.append(_fila("Todos los pares", "Floyd-Warshall", n, g.numero_aristas(), t1, k1, suma, ok))
        filas.append(_fila("Todos los pares", "Johnson", n, g.numero_aristas(), t2, k2, suma, ok))
    return filas


def comparar_cfc(tamanos):
    filas = []
    for n in tamanos:
        g = grafo_aleatorio(n, int(1.2 * n))
        c1, t1, k1 = medir(kosaraju, g)
        c2, t2, k2 = medir(tarjan, g)
        ok = {frozenset(c) for c in c1} == {frozenset(c) for c in c2}
        filas.append(_fila("Componentes fuertes", "Kosaraju", n, g.numero_aristas(), t1, k1, len(c1), ok))
        filas.append(_fila("Componentes fuertes", "Tarjan", n, g.numero_aristas(), t2, k2, len(c2), ok))
    return filas


def comparar_mst(tamanos):
    filas = []
    for n in tamanos:
        g = grafo_aleatorio(n, 4 * n, dirigido=False)
        (_, c1), t1, k1 = medir(kruskal, g)
        (_, c2), t2, k2 = medir(prim, g)
        ok = c1 == c2
        filas.append(_fila("Árbol de expansión mínima", "Kruskal", n, g.numero_aristas(), t1, k1, c1, ok))
        filas.append(_fila("Árbol de expansión mínima", "Prim", n, g.numero_aristas(), t2, k2, c2, ok))
    return filas


def comparar_flujo(tamanos):
    filas = []
    for n in tamanos:
        red, s, t = red_flujo_aleatoria(n, 4 * n)
        (f1, a1), t1, k1 = medir(ford_fulkerson, red, s, t)
        (f2, a2), t2, k2 = medir(edmonds_karp, red, s, t)
        ok = f1 == f2 and not verificar_flujo(red, s, t)
        m = red.numero_arcos()
        filas.append(_fila("Flujo máximo", "Ford-Fulkerson (DFS)", n, m, t1, k1, f"{f1} ({a1} aumentos)", ok))
        filas.append(_fila("Flujo máximo", "Edmonds-Karp", n, m, t2, k2, f"{f2} ({a2} aumentos)", ok))
    return filas


def ejecutar_comparaciones(modo="rapido"):
    tam = TAMANOS_RAPIDO if modo == "rapido" else TAMANOS_COMPLETO
    filas = []
    filas += comparar_rutas(tam["rutas"])
    filas += comparar_todos_pares(tam["todos_pares"])
    filas += comparar_cfc(tam["cfc"])
    filas += comparar_mst(tam["mst"])
    filas += comparar_flujo(tam["flujo"])
    return filas


def graficar_comparaciones(filas, archivo="comparacion_algoritmos.png"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    grupos = []
    for f in filas:
        if f["comparacion"] not in grupos:
            grupos.append(f["comparacion"])
    fig, ejes = plt.subplots(2, 3, figsize=(15, 8.5))
    ejes = ejes.ravel()
    for eje, grupo in zip(ejes, grupos):
        algoritmos = []
        for f in filas:
            if f["comparacion"] == grupo and f["algoritmo"] not in algoritmos:
                algoritmos.append(f["algoritmo"])
        for alg in algoritmos:
            datos = [f for f in filas if f["comparacion"] == grupo and f["algoritmo"] == alg]
            eje.plot([d["V"] for d in datos], [d["tiempo_ms"] for d in datos], marker="o",
                     label=f"{alg}  {COMPLEJIDAD[alg]}")
        eje.set_title(grupo)
        eje.set_xlabel("Nodos (V)")
        eje.set_ylabel("Tiempo (ms)")
        eje.grid(alpha=0.3)
        eje.legend(fontsize=8)
    for eje in ejes[len(grupos):]:
        eje.axis("off")
    fig.suptitle("Desempeño empírico de las alternativas de las guías (semilla 2026)")
    fig.tight_layout()
    ruta = ruta_reporte(archivo)
    fig.savefig(ruta, dpi=120)
    plt.close(fig)
    return ruta


# -------------------------------------------------- validación de escenarios
def validar_escenarios():
    """Casos de prueba con resultado esperado conocido.
    Devuelve lista de dicts (caso, esperado, obtenido, ok)."""
    casos = []

    def caso(nombre, esperado, obtenido):
        casos.append({"caso": nombre, "esperado": esperado, "obtenido": obtenido,
                      "ok": esperado == obtenido})

    # Módulo 1
    fisica = gr.cargar_red_fisica()
    caso("M1 · red física sin problemas de consistencia", [], fisica.validar())
    tit = gr.cargar_titularidad()
    caso("M1 · titularidad cliente-cuenta es bipartita", [], gr.validar_titularidad(tit))

    # Módulo 2
    with open(ruta_datos("patrones_esperados.json"), encoding="utf-8") as f:
        esperado = json.load(f)
    tiempos = ef.matriz_tiempos(fisica)
    cuentas = [n for n, a in tit.nodos.items() if a["tipo"] == "cuenta"]
    res = at.analizar(at.cargar_transacciones(), at.cargar_retiros(), tiempos, cuentas)
    caso("M2 · pitufeo hacia la cuenta esperada", [esperado["pitufeo"]["destino"]],
         [a["cuenta_destino"] for a in res["pitufeo"]])
    caso("M2 · ciclo de fondos entre comercializadoras", [sorted(esperado["ciclo"])],
         [g["cuentas"] for g in res["grupos"]])
    caso("M2 · cuenta puente", [esperado["cuenta_puente"]],
         [a["cuenta_puente"] for a in res["puente"]])
    caso("M2 · estratificación en 3 capas hasta la cuenta final",
         [([esperado["estratificacion"]["final"]], 3)],
         [(h["final"], h["numero_capas"]) for h in res["estratificacion"]])
    caso("M2 · viaje imposible (sin falsos positivos del turista legítimo)",
         sorted(esperado["viaje_imposible"]), sorted(a["tarjeta"] for a in res["viaje_imposible"]))

    # Módulo 3
    enr = gr.cargar_red_enrutamiento()
    r = ef.mejor_ruta(enr, "CTA_CMA_QUI", "CTA_BX_LIMA", 5000, "costo")
    caso("M3 · Quillabamba -> Lima S/ 5 000 por costo (diferida, S/ 3.50)",
         (["CTA_CMA_QUI", "CCE_DIF", "CTA_BX_LIMA"], 3.5), (r["camino"], r["costo"]))
    r = ef.mejor_ruta(enr, "CTA_CMA_QUI", "CTA_BX_LIMA", 1500, "costo")
    caso("M3 · S/ 1 500 por costo usa billetera (S/ 2.25)",
         (["CTA_CMA_QUI", "BILL_A", "CTA_BX_LIMA"], 2.25), (r["camino"], r["costo"]))
    r = ef.mejor_ruta(enr, "CTA_CMA_QUI", "CTA_BX_LIMA", 50000, "tiempo")
    caso("M3 · S/ 50 000 por tiempo excluye la inmediata (límite 30 000)",
         False, "CCE_INM" in r["camino"])
    r = ef.mejor_ruta(gr.cargar_red_enrutamiento("promo"), "CTA_CMA_QUI", "CTA_BX_LIMA", 400)
    caso("M3 · con cashback se usa Bellman-Ford y la ruta cuesta S/ -4.00",
         ("Bellman-Ford", -4.0), (r["algoritmo"].split(" ")[0], r["costo"]))
    rul = ef.detectar_ruleteo(gr.cargar_red_enrutamiento("ruleteo"), 400)
    caso("M3 · ciclo negativo de ruleteo detectado", True, rul is not None)
    caso("M3 · tiempo mínimo Plaza de Armas -> Machupicchu = 4.35 h", 4.35,
         round(tiempos["ATM_PLZ"]["ATM_MPP"], 2))

    # Módulo 4
    liq = gr.cargar_red_liquidez()
    p = dl.planificar(liq, "normal")
    caso("M4 · temporada normal: toda la demanda cubierta", 0,
         sum(d["pendiente"] for d in p["pendientes"]))
    p = dl.planificar(liq, "alta")
    caso("M4 · temporada alta: flujo válido (capacidad y conservación)", [], p["verificacion"])
    caso("M4 · temporada alta: cuello de botella en los tramos de tren a Machupicchu",
         {"OLL -> MPP", "HID -> MPP"},
         {c[1].split(" (")[0] for c in p["corte"] if c[0] == "ruta"})
    ek = dl.planificar(liq, "alta", "edmonds_karp")
    caso("M4 · Edmonds-Karp y costo mínimo distribuyen la misma cantidad",
         ek["flujo_maximo"], p["flujo_maximo"])
    caso("M4 · el plan de costo mínimo no es más caro que el de Edmonds-Karp",
         True, p["costo_total"] <= ek["costo_total"])
    huaico = dl.planificar(gr.cargar_red_liquidez([("OLL", "SMA")]), "alta")
    caso("M4 · con huaico en Abra Málaga aumenta la demanda no cubierta", True,
         sum(d["pendiente"] for d in huaico["pendientes"])
         > sum(d["pendiente"] for d in p["pendientes"]))
    t1 = dl.red_troncal(fisica, "riesgo", "kruskal")
    t2 = dl.red_troncal(fisica, "riesgo", "prim")
    caso("M4 · Kruskal y Prim: mismo riesgo total de la red troncal", t1["costo"], t2["costo"])
    criticos = dl.nodos_criticos(fisica)
    caso("M4 · nodos puente de la problemática son críticos",
         True, all(n in criticos for n in ("OLL", "URC", "URU_BR", "SMA")))
    return casos


def escenario_huaico():
    """Compara la red antes y después de cerrar Abra Málaga."""
    cierre = [("OLL", "SMA")]
    antes_f, despues_f = gr.cargar_red_fisica(), gr.cargar_red_fisica(cierre)
    t_antes, t_despues = ef.matriz_tiempos(antes_f), ef.matriz_tiempos(despues_f)
    p_antes = dl.planificar(gr.cargar_red_liquidez(), "alta")
    p_despues = dl.planificar(gr.cargar_red_liquidez(cierre), "alta")
    c_antes, c_despues = dl.nodos_criticos(antes_f), dl.nodos_criticos(despues_f)
    return {
        "tiempo_cusco_quillabamba": (t_antes["CUS_BC"]["QUI_BR"], t_despues["CUS_BC"]["QUI_BR"]),
        "flujo": (p_antes["flujo_maximo"], p_despues["flujo_maximo"]),
        "pendiente": (sum(d["pendiente"] for d in p_antes["pendientes"]),
                      sum(d["pendiente"] for d in p_despues["pendientes"])),
        "costo": (p_antes["costo_total"], p_despues["costo_total"]),
        "pendientes_despues": p_despues["pendientes"],
        "corte_despues": p_despues["corte"],
        "nuevos_criticos": sorted(set(c_despues) - set(c_antes)),
        "criticos_despues": c_despues,
    }


# ------------------------------------------------------------------ reportes
def reporte_validacion(casos):
    filas = [["OK" if c["ok"] else "FALLA", c["caso"], c["esperado"], c["obtenido"]] for c in casos]
    total = sum(c["ok"] for c in casos)
    return (f"VALIDACIÓN DE ESCENARIOS: {total}/{len(casos)} casos correctos\n"
            + formatear_tabla(filas, ["Estado", "Caso", "Esperado", "Obtenido"]))


def reporte_comparaciones(filas):
    tabla = [[f["comparacion"], f["algoritmo"], f["V"], f["E"], f["complejidad"],
              f["tiempo_ms"], f["memoria_kb"], f["resultado"], "sí" if f["coincide"] else "NO"]
             for f in filas]
    return ("COMPARACIÓN EMPÍRICA DE ALGORITMOS (tiempo con perf_counter, memoria pico con tracemalloc)\n"
            + formatear_tabla(tabla, ["Comparación", "Algoritmo", "V", "E", "Complejidad",
                                      "Tiempo ms", "Memoria KB", "Resultado", "Coinciden"]))


def reporte_huaico(h):
    L = ["ESCENARIO DE CONTINGENCIA: huaico cierra Abra Málaga (temporada alta)"]
    L.append(f"Tiempo mínimo Cusco -> Quillabamba: {h['tiempo_cusco_quillabamba'][0]:.2f} h -> "
             f"{h['tiempo_cusco_quillabamba'][1]:.2f} h (ruta por tren y Santa Teresa)")
    L.append(f"Efectivo distribuido: S/ {h['flujo'][0]:,} mil -> S/ {h['flujo'][1]:,} mil")
    L.append(f"Demanda no cubierta: S/ {h['pendiente'][0]:,} mil -> S/ {h['pendiente'][1]:,} mil")
    L.append(f"Costo de traslado: S/ {h['costo'][0]:,.2f} mil -> S/ {h['costo'][1]:,.2f} mil")
    L.append("Puntos sin abastecer después del huaico:")
    for d in h["pendientes_despues"]:
        L.append(f"  {d['nodo']}: faltan S/ {d['pendiente']:,} mil de {d['demanda']:,}")
    L.append("Cuellos de botella después del huaico (corte mínimo):")
    for tipo, desc, cap in h["corte_despues"]:
        L.append(f"  [{tipo}] {desc}: {cap:,}")
    L.append("Nodos que pasan a ser críticos: " + (", ".join(h["nuevos_criticos"]) or "ninguno"))
    return "\n".join(L)


def exportar_comparaciones(filas, nombre="comparacion_algoritmos.csv"):
    ruta = ruta_reporte(nombre)
    escribir_csv(ruta, filas, list(filas[0].keys()))
    return ruta
