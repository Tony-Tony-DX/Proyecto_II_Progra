"""Guías 9 y 10 – Rutas más cortas: Dijkstra, Bellman-Ford, Johnson y
Floyd-Warshall.

El parámetro ``peso`` de cada función puede ser:
- el nombre de un atributo de la arista (por ejemplo "tiempo_h"), o
- una función peso(origen, destino, atributos) -> número, que permite calcular
  el costo de una arista según el monto de la operación (módulo 3).

Complejidades:
- Dijkstra (heapq):  O((V + E) log V)      solo pesos no negativos
- Bellman-Ford:      O(V · E)              admite pesos negativos y detecta
                                           ciclos negativos
- Johnson:           O(V · E + V (V + E) log V)   todos los pares, disperso
- Floyd-Warshall:    O(V^3) tiempo, O(V^2) memoria  todos los pares, denso
"""

import heapq
import math


def funcion_peso(grafo, peso):
    if callable(peso):
        return peso
    if not grafo.ponderado:
        return lambda u, v, a: 1
    return lambda u, v, a: a.get(peso, 1)


def reconstruir_camino(anteriores, destino):
    """Camino desde el origen hasta ``destino`` siguiendo los anteriores.
    Devuelve [] si el destino no es alcanzable."""
    if destino not in anteriores:
        return []
    camino = []
    nodo = destino
    visitados = set()
    while nodo is not None:
        if nodo in visitados:  # protección ante ciclos negativos
            return []
        visitados.add(nodo)
        camino.append(nodo)
        nodo = anteriores[nodo]
    return camino[::-1]


# ---------------------------------------------------------------- Dijkstra
def dijkstra(grafo, origen, peso="peso", traza=None):
    """Distancias mínimas desde ``origen``. Devuelve (dist, anteriores).
    Lanza ValueError si encuentra un peso negativo, porque Dijkstra no es
    correcto en ese caso (Guía 9). ``traza`` registra cada paso (animación)."""
    w = funcion_peso(grafo, peso)
    dist = {n: math.inf for n in grafo.nodos}
    anteriores = {origen: None}
    dist[origen] = 0
    cola = [(0, 0, origen)]
    contador = 1  # desempate estable en el heap
    cerrados = set()
    while cola:
        d, _, u = heapq.heappop(cola)
        if u in cerrados:
            continue
        cerrados.add(u)
        if traza is not None:
            traza.append({"tipo": "cerrar", "nodo": u, "distancia": d,
                          "desde": anteriores.get(u)})
        for v, datos in grafo.vecinos(u):
            costo = w(u, v, datos)
            if costo < -1e-9:  # tolerancia a errores de redondeo (Johnson)
                raise ValueError(
                    f"Peso negativo en {u} -> {v}: Dijkstra no aplica, use Bellman-Ford."
                )
            nueva = d + costo
            if nueva < dist[v]:  # relajación
                if traza is not None:
                    traza.append({"tipo": "relajar", "desde": u, "nodo": v,
                                  "antes": dist[v], "distancia": nueva})
                dist[v] = nueva
                anteriores[v] = u
                heapq.heappush(cola, (nueva, contador, v))
                contador += 1
    return dist, anteriores


# ------------------------------------------------------------- Bellman-Ford
def bellman_ford(grafo, origen=None, peso="peso"):
    """Bellman-Ford. Si ``origen`` es None, todas las distancias inician en 0,
    lo que equivale a agregar un nodo auxiliar conectado a todos con peso 0
    (como en Johnson) y sirve para buscar ciclos negativos en toda la red.

    Devuelve (dist, anteriores, ciclo_negativo); ciclo_negativo es una lista
    de nodos [a, b, ..., a] o None si no existe."""
    w = funcion_peso(grafo, peso)
    aristas = [(u, v, w(u, v, d)) for u in grafo.adyacencia
               for v, d in grafo.adyacencia[u].items()]
    if origen is None:
        dist = {n: 0 for n in grafo.nodos}
        anteriores = {n: None for n in grafo.nodos}
    else:
        dist = {n: math.inf for n in grafo.nodos}
        dist[origen] = 0
        anteriores = {origen: None}

    for _ in range(grafo.numero_nodos() - 1):
        cambio = False
        for u, v, costo in aristas:
            if dist[u] != math.inf and dist[u] + costo < dist[v]:
                dist[v] = dist[u] + costo
                anteriores[v] = u
                cambio = True
        if not cambio:
            break

    # Una relajación más: si todavía mejora, hay un ciclo negativo.
    for u, v, costo in aristas:
        if dist[u] != math.inf and dist[u] + costo < dist[v]:
            anteriores[v] = u
            ciclo = _extraer_ciclo(anteriores, v, grafo.numero_nodos())
            return dist, anteriores, ciclo or [v, v]
    return dist, anteriores, None


def _extraer_ciclo(anteriores, nodo, n):
    # Retroceder n veces garantiza caer dentro del ciclo.
    for _ in range(n):
        nodo = anteriores.get(nodo)
        if nodo is None:
            return None
    ciclo = [nodo]
    actual = anteriores[nodo]
    while actual != nodo:
        ciclo.append(actual)
        actual = anteriores[actual]
    ciclo.append(nodo)
    return ciclo[::-1]


# ----------------------------------------------------------- Floyd-Warshall
def floyd_warshall(grafo, peso="peso", traza=None):
    """Caminos mínimos entre todos los pares (Guía 10).
    Devuelve (orden, dist, siguiente): ``orden`` es la lista de nodos que indexa
    las matrices y ``siguiente[i][j]`` permite reconstruir el camino.
    ``traza`` guarda la matriz después de cada nodo intermedio k (solo para
    redes pequeñas: ocupa O(V^3))."""
    w = funcion_peso(grafo, peso)
    orden = list(grafo.nodos)
    indice = {n: i for i, n in enumerate(orden)}
    n = len(orden)
    dist = [[math.inf] * n for _ in range(n)]
    siguiente = [[None] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
        siguiente[i][i] = i
    for u in grafo.adyacencia:
        for v, datos in grafo.adyacencia[u].items():
            i, j = indice[u], indice[v]
            costo = w(u, v, datos)
            if costo < dist[i][j]:
                dist[i][j] = costo
                siguiente[i][j] = j

    if traza is not None:
        traza.append({"tipo": "inicio", "matriz": [fila[:] for fila in dist], "cambios": []})
    for k in range(n):
        fila_k = dist[k]
        cambios = []
        for i in range(n):
            dik = dist[i][k]
            if dik == math.inf:
                continue
            fila_i = dist[i]
            sig_i = siguiente[i]
            for j in range(n):
                nueva = dik + fila_k[j]
                if nueva < fila_i[j]:
                    fila_i[j] = nueva
                    sig_i[j] = sig_i[k]
                    if traza is not None:
                        cambios.append([i, j])
        if traza is not None:
            traza.append({"tipo": "intermedio", "k": orden[k],
                          "matriz": [fila[:] for fila in dist], "cambios": cambios})
    return orden, dist, siguiente


def ciclo_negativo_floyd(dist):
    """Hay un ciclo negativo si algún dist[i][i] < 0."""
    return any(dist[i][i] < 0 for i in range(len(dist)))


def camino_floyd(orden, siguiente, origen, destino):
    indice = {n: i for i, n in enumerate(orden)}
    i, j = indice[origen], indice[destino]
    if siguiente[i][j] is None:
        return []
    camino = [origen]
    while i != j:
        i = siguiente[i][j]
        camino.append(orden[i])
        if len(camino) > len(orden):
            return []
    return camino


# ------------------------------------------------------------------ Johnson
def johnson(grafo, peso="peso"):
    """Caminos mínimos entre todos los pares en grafos dispersos (Guía 9).
    1) Bellman-Ford desde un nodo auxiliar para obtener potenciales h(v).
    2) Reponderar: w'(u, v) = w(u, v) + h(u) - h(v) >= 0.
    3) Dijkstra desde cada nodo con w'.
    4) Deshacer la reponderación.
    Devuelve {origen: {destino: distancia}}."""
    w = funcion_peso(grafo, peso)
    h, _, ciclo = bellman_ford(grafo, None, w)
    if ciclo:
        raise ValueError(f"Ciclo negativo detectado: {' -> '.join(ciclo)}")

    def reponderado(u, v, datos):
        return w(u, v, datos) + h[u] - h[v]

    resultado = {}
    for u in grafo.nodos:
        dist, _ = dijkstra(grafo, u, reponderado)
        resultado[u] = {
            v: (d - h[u] + h[v]) if d != math.inf else math.inf
            for v, d in dist.items()
        }
    return resultado
