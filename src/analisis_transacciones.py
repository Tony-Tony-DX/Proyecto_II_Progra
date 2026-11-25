"""Módulo 2 – Análisis de transacciones y detección de operaciones sospechosas.

Las transacciones se guardan como un REGISTRO DE EVENTOS (cada operación con su
monto, fecha y hora) y a partir de él se construye el grafo dirigido de
cuentas, agregando monto total y número de operaciones por par de cuentas.

Patrón -> algoritmo (todos de las guías):
- Proximidad a cuentas marcadas  -> BFS por niveles (G7)
- Rastreo de fondos              -> DFS (G7)
- Grupos de cuentas              -> Tarjan / Kosaraju (G7)
- Ciclos de fondos               -> DFS dentro de cada componente fuerte (G7)
- Estratificación por capas      -> orden topológico del grafo condensado (G7)
- Pitufeo y cuentas puente       -> conteo de entradas/salidas en ventanas de tiempo
- Viaje imposible de tarjetas    -> tiempos mínimos de Floyd-Warshall (G10)

IMPORTANTE: los resultados son indicadores para revisión; la detección de un
patrón no constituye prueba de fraude ni de lavado de activos.
"""

from collections import defaultdict
from datetime import datetime, timedelta

from src.algoritmos.recorridos import (bfs_niveles, capas_topologicas, ciclos_simples,
                                       grafo_condensado, kosaraju, rastrear_caminos, tarjan)
from src.graph import ErrorValidacion, Grafo
from src.utils import escribir_csv, leer_csv, ruta_datos, ruta_reporte

UMBRAL_MONTO = 3000        # umbral simulado de registro de operaciones (soles)
UMBRAL_ALTO_VALOR = 10000  # transferencias consideradas de alto valor
AVISO = ("Los patrones reportados son INDICADORES para revisión por el área de "
         "cumplimiento; no constituyen prueba de fraude ni de lavado de activos.")


# ------------------------------------------------------------------- carga
def _fecha(texto):
    return datetime.strptime(texto, "%Y-%m-%d %H:%M")


def cargar_transacciones(ruta=None):
    eventos = leer_csv(ruta or ruta_datos("transacciones.csv"))
    for e in eventos:
        e["origen"], e["destino"] = str(e["origen"]), str(e["destino"])
        e["fecha"] = _fecha(e["fecha_hora"])
        if not isinstance(e["monto"], (int, float)) or e["monto"] <= 0:
            raise ErrorValidacion(f"Monto inválido en {e.get('id')}: {e['monto']}")
    return eventos


def cargar_retiros(ruta=None):
    retiros = leer_csv(ruta or ruta_datos("retiros_atm.csv"))
    for r in retiros:
        r["fecha"] = _fecha(r["fecha_hora"])
    return retiros


def construir_grafo(eventos, cuentas_validas=None):
    """Grafo dirigido de cuentas. Si se pasan ``cuentas_validas`` (de la
    titularidad), una transacción con una cuenta desconocida se rechaza."""
    grafo = Grafo(dirigido=True, ponderado=True, nombre="Transacciones entre cuentas")
    for c in sorted(cuentas_validas or []):
        grafo.agregar_nodo(c)
    for e in eventos:
        u, v = e["origen"], e["destino"]
        for n in (u, v):
            if n not in grafo:
                if cuentas_validas is not None:
                    raise ErrorValidacion(f"Transacción {e.get('id')}: la cuenta '{n}' "
                                          "no figura en la titularidad.")
                grafo.agregar_nodo(n)
        if grafo.existe_arista(u, v):
            a = grafo.adyacencia[u][v]
            a["monto_total"] = round(a["monto_total"] + e["monto"], 2)
            a["n_operaciones"] += 1
            a["ultima"] = e["fecha_hora"]
        else:
            grafo.agregar_arista(u, v, monto_total=e["monto"], n_operaciones=1,
                                 primera=e["fecha_hora"], ultima=e["fecha_hora"])
    return grafo


# --------------------------------------------------------------- recorridos
def proximidad(grafo, marcadas, max_nivel=2):
    """Cuentas a 1, 2, ... saltos de las cuentas marcadas (sin importar el
    sentido de la transferencia). Devuelve {nivel: [cuentas]}."""
    niveles = bfs_niveles(grafo.vista_no_dirigida(), marcadas, max_nivel)
    por_nivel = defaultdict(list)
    for cuenta, nivel in niveles.items():
        if nivel > 0:
            por_nivel[nivel].append(cuenta)
    return {n: sorted(c) for n, c in sorted(por_nivel.items())}


def rastrear(grafo, origen, max_profundidad=5, monto_minimo=0):
    """Recorridos de los fondos que salen de ``origen`` (DFS). Devuelve
    (caminos, intermediarios, receptores_finales)."""
    caminos = rastrear_caminos(
        grafo, origen, max_profundidad,
        filtro=lambda u, v, a: a.get("monto_total", 0) >= monto_minimo)
    intermediarios = sorted({n for c in caminos for n in c[1:-1]})
    receptores = sorted({c[-1] for c in caminos})
    return caminos, intermediarios, receptores


def grupos_y_ciclos(grafo, algoritmo="tarjan", max_longitud=8):
    """Componentes fuertemente conexas de 2 o más cuentas (el dinero puede
    volver a su origen) y los ciclos simples dentro de cada una."""
    componentes = (tarjan if algoritmo == "tarjan" else kosaraju)(grafo)
    resultado = []
    for comp in componentes:
        if len(comp) < 2:
            continue
        miembros = set(comp)
        monto = sum(a["monto_total"] for u in comp for v, a in grafo.vecinos(u)
                    if v in miembros)
        resultado.append({
            "cuentas": sorted(comp),
            "monto_interno": round(monto, 2),
            "ciclos": ciclos_simples(grafo, comp, max_longitud),
        })
    return resultado


def estratificacion(grafo, umbral=UMBRAL_ALTO_VALOR, min_capas=3):
    """Capas de cuentas por las que pasa el dinero de alto valor.

    1) Se conservan solo las transferencias de alto valor.
    2) Se contraen las componentes fuertes (Tarjan) -> grafo condensado (DAG).
    3) Orden topológico -> capa de cada nodo = camino más largo desde una fuente.
    Una cuenta en la capa >= ``min_capas`` recibió dinero que pasó por varias
    capas de intermediarios."""
    alto = grafo.filtrar_aristas(lambda u, v, a: a.get("monto_total", 0) >= umbral)
    activos = {u for u, v, _ in alto.aristas()} | {v for u, v, _ in alto.aristas()}
    sub = Grafo(True, True, "alto valor")
    for n in activos:
        sub.agregar_nodo(n)
    for u, v, a in alto.aristas():
        sub.agregar_arista(u, v, **a)

    componentes = tarjan(sub)
    dag, mapa = grafo_condensado(sub, componentes)
    capa = capas_topologicas(dag)
    transpuesto = dag.transpuesto()
    miembros = defaultdict(list)
    for cuenta, c in mapa.items():
        miembros[c].append(cuenta)

    hallazgos = []
    for c, nivel in capa.items():
        if nivel < min_capas:
            continue
        ancestros = bfs_niveles(transpuesto, [c])
        capas = defaultdict(list)
        for anc in ancestros:
            capas[capa[anc]].extend(miembros[anc])
        hallazgos.append({
            "final": sorted(miembros[c]),
            "numero_capas": nivel,
            "capas": {k: sorted(v) for k, v in sorted(capas.items())},
            "origenes": sorted(n for a in ancestros if capa[a] == 0 for n in miembros[a]),
        })
    return hallazgos


# ----------------------------------------------------------- ventanas de tiempo
def pitufeo(eventos, umbral=UMBRAL_MONTO, fraccion=0.8, ventana_h=72,
            min_operaciones=10, min_emisores=5):
    """Muchas entradas fraccionadas justo por debajo del umbral hacia una misma
    cuenta, desde varias cuentas, dentro de una ventana de tiempo.
    Ventana deslizante con dos punteros: O(n log n) por el ordenamiento."""
    por_destino = defaultdict(list)
    for e in eventos:
        if fraccion * umbral <= e["monto"] < umbral:
            por_destino[e["destino"]].append(e)
    ventana = timedelta(hours=ventana_h)
    alertas = []
    for destino, lista in por_destino.items():
        lista.sort(key=lambda e: e["fecha"])
        mejor = None
        j = 0
        for i in range(len(lista)):
            while lista[i]["fecha"] - lista[j]["fecha"] > ventana:
                j += 1
            bloque = lista[j:i + 1]
            emisores = {e["origen"] for e in bloque}
            if len(bloque) >= min_operaciones and len(emisores) >= min_emisores:
                if mejor is None or len(bloque) > len(mejor):
                    mejor = bloque
        if mejor:
            alertas.append({
                "cuenta_destino": destino,
                "operaciones": len(mejor),
                "emisores": sorted({e["origen"] for e in mejor}),
                "monto_total": round(sum(e["monto"] for e in mejor), 2),
                "desde": mejor[0]["fecha_hora"], "hasta": mejor[-1]["fecha_hora"],
                "agencias": sorted({e["agencia"] for e in mejor}),
            })
    return alertas


def cuentas_puente(eventos, monto_minimo=20000, ventana_h=12, proporcion=0.8,
                   min_receptores=2):
    """Cuenta que recibe un monto alto y reenvía casi todo a varias cuentas en
    pocas horas."""
    salidas = defaultdict(list)
    for e in eventos:
        salidas[e["origen"]].append(e)
    ventana = timedelta(hours=ventana_h)
    alertas = []
    for e in eventos:
        if e["monto"] < monto_minimo:
            continue
        cuenta = e["destino"]
        reenvios = [s for s in salidas[cuenta]
                    if e["fecha"] < s["fecha"] <= e["fecha"] + ventana]
        total = sum(s["monto"] for s in reenvios)
        receptores = {s["destino"] for s in reenvios}
        if total >= proporcion * e["monto"] and len(receptores) >= min_receptores:
            horas = (max(s["fecha"] for s in reenvios) - e["fecha"]).total_seconds() / 3600
            alertas.append({
                "cuenta_puente": cuenta, "recibido": e["monto"], "de": e["origen"],
                "reenviado": round(total, 2), "porcentaje": round(100 * total / e["monto"], 1),
                "receptores": sorted(receptores), "horas": round(horas, 1),
            })
    return alertas


def viaje_imposible(retiros, tiempos_h):
    """Dos retiros consecutivos de la misma tarjeta en cajeros distintos con
    menos tiempo entre ellos que el mínimo necesario para viajar (calculado con
    Floyd-Warshall sobre la red física)."""
    por_tarjeta = defaultdict(list)
    for r in retiros:
        por_tarjeta[r["tarjeta"]].append(r)
    alertas = []
    for tarjeta, lista in por_tarjeta.items():
        lista.sort(key=lambda r: r["fecha"])
        for a, b in zip(lista, lista[1:]):
            if a["cajero"] == b["cajero"]:
                continue
            transcurrido = (b["fecha"] - a["fecha"]).total_seconds() / 3600
            minimo = tiempos_h[a["cajero"]][b["cajero"]]
            if transcurrido < minimo:
                alertas.append({
                    "tarjeta": tarjeta, "cajero_1": a["cajero"], "fecha_1": a["fecha_hora"],
                    "cajero_2": b["cajero"], "fecha_2": b["fecha_hora"],
                    "horas_transcurridas": round(transcurrido, 2),
                    "horas_minimas_viaje": round(minimo, 2),
                })
    return alertas


# ------------------------------------------------------------------ análisis
def analizar(eventos, retiros, tiempos_h, cuentas_validas=None):
    grafo = construir_grafo(eventos, cuentas_validas)
    res = {
        "grafo": grafo,
        "pitufeo": pitufeo(eventos),
        "puente": cuentas_puente(eventos),
        "grupos": grupos_y_ciclos(grafo),
        "estratificacion": estratificacion(grafo),
        "viaje_imposible": viaje_imposible(retiros, tiempos_h),
    }
    marcadas = set()
    for a in res["pitufeo"]:
        marcadas.add(a["cuenta_destino"])
    for a in res["puente"]:
        marcadas.add(a["cuenta_puente"])
    for g in res["grupos"]:
        marcadas.update(g["cuentas"])
    for h in res["estratificacion"]:
        marcadas.update(h["final"])
    res["marcadas"] = sorted(marcadas)
    res["proximidad"] = proximidad(grafo, marcadas, max_nivel=2)
    return res


def generar_reporte(res):
    g = res["grafo"]
    L = []
    L.append("REPORTE DE ANÁLISIS DE TRANSACCIONES – Caja Municipal Andina (datos simulados)")
    L.append(AVISO)
    L.append(f"Red analizada: {g.numero_nodos()} cuentas, {g.numero_aristas()} relaciones.")

    L.append("\n1. PITUFEO (depósitos fraccionados bajo el umbral de S/ "
             f"{UMBRAL_MONTO:,})")
    for a in res["pitufeo"] or [None]:
        if a is None:
            L.append("   Sin alertas.")
            break
        L.append(f"   Cuenta {a['cuenta_destino']}: {a['operaciones']} depósitos de "
                 f"{len(a['emisores'])} cuentas entre {a['desde']} y {a['hasta']}, "
                 f"total S/ {a['monto_total']:,.2f}. Agencias: {', '.join(a['agencias'])}")
        L.append(f"     Emisores: {', '.join(a['emisores'])}")

    L.append("\n2. CIRCULACIÓN DE FONDOS (componentes fuertemente conexas – Tarjan)")
    for grupo in res["grupos"] or [None]:
        if grupo is None:
            L.append("   Sin alertas.")
            break
        L.append(f"   Grupo {', '.join(grupo['cuentas'])}: S/ {grupo['monto_interno']:,.2f} "
                 "circulando dentro del grupo")
        for c in grupo["ciclos"]:
            L.append("     Ciclo: " + " -> ".join(c))

    L.append("\n3. CUENTAS PUENTE")
    for a in res["puente"] or [None]:
        if a is None:
            L.append("   Sin alertas.")
            break
        L.append(f"   {a['cuenta_puente']} recibió S/ {a['recibido']:,.2f} de {a['de']} y "
                 f"reenvió {a['porcentaje']} % en {a['horas']} h a {', '.join(a['receptores'])}")

    L.append(f"\n4. ESTRATIFICACIÓN (transferencias >= S/ {UMBRAL_ALTO_VALOR:,}, "
             "orden topológico del grafo condensado)")
    for h in res["estratificacion"] or [None]:
        if h is None:
            L.append("   Sin alertas.")
            break
        L.append(f"   Destino final {', '.join(h['final'])}: el dinero pasó por "
                 f"{h['numero_capas']} capas desde {', '.join(h['origenes'])}")
        for k, cuentas in h["capas"].items():
            L.append(f"     Capa {k}: {', '.join(cuentas)}")

    L.append("\n5. VIAJE IMPOSIBLE DE TARJETAS (tiempos mínimos con Floyd-Warshall)")
    for a in res["viaje_imposible"] or [None]:
        if a is None:
            L.append("   Sin alertas.")
            break
        L.append(f"   Tarjeta {a['tarjeta']}: {a['cajero_1']} ({a['fecha_1']}) -> "
                 f"{a['cajero_2']} ({a['fecha_2']}): {a['horas_transcurridas']} h, "
                 f"pero el viaje mínimo toma {a['horas_minimas_viaje']} h")

    L.append("\n6. PROXIMIDAD A CUENTAS MARCADAS (BFS por niveles)")
    L.append(f"   Cuentas marcadas: {', '.join(res['marcadas'])}")
    for nivel, cuentas in res["proximidad"].items():
        L.append(f"   A {nivel} salto(s): {len(cuentas)} cuentas -> "
                 f"{', '.join(cuentas[:20])}{' ...' if len(cuentas) > 20 else ''}")
    return "\n".join(L)


def exportar_alertas(res, nombre="alertas_transacciones.csv"):
    filas = []
    for a in res["pitufeo"]:
        filas.append({"patron": "pitufeo", "cuentas": a["cuenta_destino"],
                      "detalle": f"{a['operaciones']} depósitos de {len(a['emisores'])} emisores",
                      "monto": a["monto_total"]})
    for gpo in res["grupos"]:
        filas.append({"patron": "ciclo", "cuentas": " ".join(gpo["cuentas"]),
                      "detalle": f"{len(gpo['ciclos'])} ciclo(s)", "monto": gpo["monto_interno"]})
    for a in res["puente"]:
        filas.append({"patron": "cuenta_puente", "cuentas": a["cuenta_puente"],
                      "detalle": f"reenvió {a['porcentaje']} % en {a['horas']} h",
                      "monto": a["recibido"]})
    for h in res["estratificacion"]:
        filas.append({"patron": "estratificacion", "cuentas": " ".join(h["final"]),
                      "detalle": f"{h['numero_capas']} capas desde {' '.join(h['origenes'])}",
                      "monto": ""})
    for a in res["viaje_imposible"]:
        filas.append({"patron": "viaje_imposible", "cuentas": a["tarjeta"],
                      "detalle": f"{a['cajero_1']} -> {a['cajero_2']} en "
                                 f"{a['horas_transcurridas']} h (mínimo {a['horas_minimas_viaje']} h)",
                      "monto": ""})
    ruta = ruta_reporte(nombre)
    escribir_csv(ruta, filas, ["patron", "cuentas", "detalle", "monto"])
    return ruta
