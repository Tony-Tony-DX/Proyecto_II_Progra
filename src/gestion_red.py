"""Módulo 1 – Gestión y modelamiento de redes financieras.

Carga, valida, guarda y visualiza las redes de la Caja Municipal Andina sobre
la estructura común ``Grafo``.

Formatos admitidos:
- CSV  con encabezado (nodos: columna ``id``; aristas: ``origen`` y ``destino``)
- TXT  una arista por línea: ``origen destino [peso]`` (líneas con # se ignoran)
- JSON {"dirigido": bool, "ponderado": bool, "nodos": [...], "aristas": [...]}
"""

import json
import math

from src.algoritmos.recorridos import componentes_conexas, es_bipartito
from src.graph import ErrorValidacion, Grafo
from src.utils import leer_csv, ruta_datos, ruta_reporte

ATRIBUTOS_NODO_NUMERICOS = ("oferta", "almacenamiento", "demanda_normal", "demanda_alta")


# ------------------------------------------------------------------ carga
def cargar_nodos_csv(grafo, ruta):
    """Agrega los nodos de un CSV. Devuelve la cantidad cargada."""
    total = 0
    for fila in leer_csv(ruta):
        nodo = fila.pop("id", None)
        if nodo is None:
            raise ErrorValidacion(f"Fila sin 'id' en {ruta}.")
        atributos = {k: v for k, v in fila.items() if v is not None}
        grafo.agregar_nodo(nodo, **atributos)
        total += 1
    return total


def cargar_aristas_csv(grafo, ruta, crear_nodos=False):
    """Agrega las aristas de un CSV. Si ``crear_nodos`` es False (por defecto),
    una arista hacia un nodo no registrado se rechaza."""
    total = 0
    for numero, fila in enumerate(leer_csv(ruta), start=2):
        origen, destino = fila.pop("origen", None), fila.pop("destino", None)
        if origen is None or destino is None:
            raise ErrorValidacion(f"{ruta}, línea {numero}: falta origen o destino.")
        origen, destino = str(origen), str(destino)
        for n in (origen, destino):
            if n not in grafo:
                if not crear_nodos:
                    raise ErrorValidacion(f"{ruta}, línea {numero}: el nodo '{n}' no existe.")
                grafo.agregar_nodo(n)
        atributos = {k: v for k, v in fila.items() if v is not None}
        try:
            grafo.agregar_arista(origen, destino, **atributos)
        except ErrorValidacion as e:
            raise ErrorValidacion(f"{ruta}, línea {numero}: {e}") from None
        total += 1
    return total


def cargar_txt(ruta, dirigido=True):
    """Lee aristas ``origen destino [peso]``. Si ninguna línea trae peso, el
    grafo resultante es no ponderado."""
    lineas = []
    with open(ruta, encoding="utf-8") as f:
        for numero, linea in enumerate(f, start=1):
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            partes = linea.split()
            if len(partes) not in (2, 3):
                raise ErrorValidacion(f"{ruta}, línea {numero}: formato inválido '{linea}'.")
            lineas.append((numero, partes))
    ponderado = any(len(p) == 3 for _, p in lineas)
    grafo = Grafo(dirigido=dirigido, ponderado=ponderado, nombre=ruta)
    for numero, partes in lineas:
        for n in partes[:2]:
            if n not in grafo:
                grafo.agregar_nodo(n)
        atributos = {}
        if len(partes) == 3:
            try:
                atributos["peso"] = float(partes[2])
            except ValueError:
                raise ErrorValidacion(f"{ruta}, línea {numero}: peso no numérico.") from None
        grafo.agregar_arista(partes[0], partes[1], **atributos)
    return grafo


def cargar_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    grafo = Grafo(datos.get("dirigido", True), datos.get("ponderado", True),
                  datos.get("nombre", ruta))
    for nodo in datos.get("nodos", []):
        nodo = dict(nodo)
        grafo.agregar_nodo(nodo.pop("id"), **nodo)
    for arista in datos.get("aristas", []):
        arista = dict(arista)
        grafo.agregar_arista(arista.pop("origen"), arista.pop("destino"), **arista)
    return grafo


def guardar_json(grafo, ruta):
    datos = {
        "nombre": grafo.nombre,
        "dirigido": grafo.dirigido,
        "ponderado": grafo.ponderado,
        "nodos": [{"id": n, **a} for n, a in grafo.nodos.items()],
        "aristas": [{"origen": u, "destino": v, **a} for u, v, a in grafo.aristas()],
    }
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    return ruta


# --------------------------------------------- redes de la Caja Municipal Andina
def cargar_red_fisica(cerrar=None):
    """Red vial y ferroviaria: no dirigida y ponderada (distancia, tiempo, riesgo).
    ``cerrar`` es una lista de pares (u, v) de tramos cerrados (por ejemplo, un
    huaico en Abra Málaga)."""
    grafo = Grafo(dirigido=False, ponderado=True, nombre="Red física CMA")
    cargar_nodos_csv(grafo, ruta_datos("nodos.csv"))
    cargar_aristas_csv(grafo, ruta_datos("rutas_fisicas.csv"))
    for u, v in cerrar or []:
        grafo.eliminar_arista(u, v)
    return grafo


def cargar_red_liquidez(cerrar=None):
    """Red de traslado de efectivo: dirigida. Las rutas con sentido "doble" se
    convierten en dos arcos con la misma capacidad."""
    grafo = Grafo(dirigido=True, ponderado=True, nombre="Red de liquidez CMA")
    cargar_nodos_csv(grafo, ruta_datos("nodos.csv"))
    cerradas = {frozenset(p) for p in cerrar or []}
    for numero, fila in enumerate(leer_csv(ruta_datos("distribucion_liquidez.csv")), start=2):
        u, v = fila.pop("origen"), fila.pop("destino")
        sentido = fila.pop("sentido", "doble")
        if frozenset((u, v)) in cerradas:
            continue
        for n in (u, v):
            if n not in grafo:
                raise ErrorValidacion(f"distribucion_liquidez.csv, línea {numero}: "
                                      f"el nodo '{n}' no existe.")
        grafo.agregar_arista(u, v, **fila)
        if sentido == "doble":
            grafo.agregar_arista(v, u, **fila)
    return grafo


def cargar_red_enrutamiento(variante=None):
    """Red de canales de operación: dirigida y ponderada.
    ``variante`` puede ser "promo" o "ruleteo": sus filas modifican o agregan
    aristas sobre la red base (campañas de cashback)."""
    grafo = Grafo(dirigido=True, ponderado=True, nombre="Red de enrutamiento CMA")
    cargar_nodos_csv(grafo, ruta_datos("nodos_enrutamiento.csv"))
    cargar_aristas_csv(grafo, ruta_datos("red_enrutamiento.csv"))
    if variante:
        for fila in leer_csv(ruta_datos(f"red_enrutamiento_{variante}.csv")):
            u, v = fila.pop("origen"), fila.pop("destino")
            if grafo.existe_arista(u, v):
                grafo.modificar_arista(u, v, **fila)
            else:
                grafo.agregar_arista(u, v, **fila)
    return grafo


def cargar_titularidad():
    """Grafo cliente - cuenta: no dirigido y no ponderado (bipartito)."""
    grafo = Grafo(dirigido=False, ponderado=False, nombre="Titularidad cliente - cuenta")
    for fila in leer_csv(ruta_datos("titularidad.csv")):
        cliente, cuenta = fila["cliente"], fila["cuenta"]
        if cliente not in grafo:
            grafo.agregar_nodo(cliente, tipo="cliente", tipo_cliente=fila["tipo_cliente"])
        if cuenta in grafo:
            raise ErrorValidacion(f"La cuenta '{cuenta}' aparece con más de un titular "
                                  "o coincide con el código de un cliente.")
        grafo.agregar_nodo(cuenta, tipo="cuenta", agencia=fila["agencia"])
        grafo.agregar_arista(cliente, cuenta)
    return grafo


# ------------------------------------------------------------- validación
def validar_titularidad(grafo):
    """El grafo cliente - cuenta debe ser bipartito y cada lado debe tener un
    único tipo de nodo. Devuelve la lista de problemas."""
    problemas = grafo.validar()
    ok, _, _, conflicto = es_bipartito(grafo)
    if not ok:
        problemas.append(f"El grafo de titularidad no es bipartito (conflicto {conflicto}).")
        return problemas
    for u, v, _ in grafo.aristas():
        if grafo.nodos[u].get("tipo") == grafo.nodos[v].get("tipo"):
            problemas.append(f"Relación inválida entre dos nodos del mismo tipo: {u} - {v}.")
    return problemas


def resumen(grafo):
    tipos = {}
    for a in grafo.nodos.values():
        tipos[a.get("tipo", "sin tipo")] = tipos.get(a.get("tipo", "sin tipo"), 0) + 1
    lineas = [repr(grafo)]
    lineas.append("Nodos por tipo: " + ", ".join(f"{t}={c}" for t, c in sorted(tipos.items())))
    lineas.append(f"Componentes conexas: {len(componentes_conexas(grafo))}")
    problemas = grafo.validar()
    lineas.append("Validación: " + ("sin problemas" if not problemas else f"{len(problemas)} problemas"))
    lineas.extend("  - " + p for p in problemas[:10])
    return "\n".join(lineas)


# ----------------------------------------------------------- visualización
COLORES_TIPO = {
    "boveda_central": "#8e2a2a", "boveda_regional": "#c97a2c", "agencia": "#2f5d8a",
    "cajero": "#5a8fc2", "agente": "#3f8f6b", "paso": "#a3a8b0",
}


def _posiciones(grafo):
    if all("lat" in a and "lon" in a for a in grafo.nodos.values()):
        return {n: (a["lon"], a["lat"]) for n, a in grafo.nodos.items()}
    n = max(len(grafo.nodos), 1)
    return {nodo: (math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n))
            for i, nodo in enumerate(grafo.nodos)}


def visualizar(grafo, archivo="red.png", titulo=None, resaltar_aristas=None,
               resaltar_nodos=None, etiquetas_aristas=None):
    """Dibuja la red con matplotlib y la guarda en reportes/. Si los nodos
    tienen lat/lon se dibujan sobre un mapa esquemático; si no, en círculo."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pos = _posiciones(grafo)
    resaltar_aristas = {frozenset(e) if not grafo.dirigido else tuple(e)
                        for e in (resaltar_aristas or [])}
    resaltar_nodos = set(resaltar_nodos or [])
    fig, ax = plt.subplots(figsize=(11, 8.5))
    for u, v, a in grafo.aristas():
        clave = frozenset((u, v)) if not grafo.dirigido else (u, v)
        x = [pos[u][0], pos[v][0]]
        y = [pos[u][1], pos[v][1]]
        if clave in resaltar_aristas:
            ax.plot(x, y, color="#c0392b", linewidth=3, zorder=2)
        elif a.get("tipo_via") == "tren":
            ax.plot(x, y, color="#d07a2a", linewidth=2, linestyle="--", zorder=1)
        else:
            ax.plot(x, y, color="#9aa0a8", linewidth=1.2, zorder=1)
        if etiquetas_aristas and clave in etiquetas_aristas:
            ax.text((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, etiquetas_aristas[clave],
                    fontsize=7, color="#6b2a2a", ha="center")
    for n, a in grafo.nodos.items():
        color = COLORES_TIPO.get(a.get("tipo"), "#2f5d8a")
        borde = "#c0392b" if n in resaltar_nodos else "white"
        tam = 220 if a.get("tipo", "").startswith("boveda") else 90
        ax.scatter(*pos[n], s=tam, color=color, edgecolors=borde,
                   linewidths=2.5 if n in resaltar_nodos else 0.8, zorder=3)
        ax.annotate(n, pos[n], fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.set_title(titulo or grafo.nombre)
    ax.set_aspect("equal", adjustable="datalim")
    ax.axis("off")
    ruta = ruta_reporte(archivo)
    fig.savefig(ruta, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return ruta
