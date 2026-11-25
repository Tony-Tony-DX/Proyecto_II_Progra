"""Guía 7 – Recorridos de grafos: BFS, DFS y sus aplicaciones.

Complejidades (V = nodos, E = aristas):
- BFS, DFS, orden topológico, Kosaraju, Tarjan, bipartición: O(V + E)
- Puntos críticos por eliminación + BFS:                     O(V · (V + E))
- Enumeración de caminos simples con DFS:                     exponencial en el
  peor caso; se acota con número máximo de saltos y poda por costo.
"""

from collections import deque

from src.graph import Grafo


# --------------------------------------------------------------------- BFS
def bfs(grafo, inicio, traza=None):
    """Orden de visita BFS desde ``inicio`` (cola FIFO).
    Si se pasa una lista ``traza``, se registra cada paso (para animarlo)."""
    visitados = {inicio}
    cola = deque([inicio])
    orden = []
    nivel = {inicio: 0}
    while cola:
        nodo = cola.popleft()
        orden.append(nodo)
        if traza is not None:
            traza.append({"tipo": "visitar", "nodo": nodo, "nivel": nivel[nodo]})
        for vecino, _ in grafo.vecinos(nodo):
            if vecino not in visitados:
                visitados.add(vecino)
                nivel[vecino] = nivel[nodo] + 1
                cola.append(vecino)
                if traza is not None:
                    traza.append({"tipo": "descubrir", "nodo": vecino, "desde": nodo,
                                  "nivel": nivel[vecino], "cola": list(cola)})
    return orden


def bfs_niveles(grafo, origenes, max_nivel=None):
    """BFS desde varios orígenes a la vez. Devuelve {nodo: nivel}, donde el
    nivel es el menor número de saltos hasta el origen más cercano."""
    nivel = {}
    cola = deque()
    for o in origenes:
        if o in grafo and o not in nivel:
            nivel[o] = 0
            cola.append(o)
    while cola:
        nodo = cola.popleft()
        if max_nivel is not None and nivel[nodo] >= max_nivel:
            continue
        for vecino, _ in grafo.vecinos(nodo):
            if vecino not in nivel:
                nivel[vecino] = nivel[nodo] + 1
                cola.append(vecino)
    return nivel


def componentes_conexas(grafo, excluir=None):
    """Componentes conexas con BFS (en grafos dirigidos se ignora el sentido).
    ``excluir`` permite simular la eliminación de un nodo sin copiar el grafo."""
    g = grafo if not grafo.dirigido else grafo.vista_no_dirigida()
    visitados = set()
    if excluir is not None:
        visitados.add(excluir)
    componentes = []
    for inicio in g.nodos:
        if inicio in visitados:
            continue
        visitados.add(inicio)
        cola = deque([inicio])
        componente = []
        while cola:
            nodo = cola.popleft()
            componente.append(nodo)
            for vecino, _ in g.vecinos(nodo):
                if vecino not in visitados:
                    visitados.add(vecino)
                    cola.append(vecino)
        componentes.append(componente)
    return componentes


def es_conexo(grafo):
    return len(componentes_conexas(grafo)) <= 1


def puntos_criticos(grafo):
    """Nodos cuya eliminación desconecta la red.

    Método (solo con BFS de la Guía 7): se elimina cada nodo por turno y se
    cuentan las componentes conexas. Si aumentan, el nodo es crítico.
    Devuelve {nodo: [nodos que quedan separados del bloque principal]}.
    """
    g = grafo if not grafo.dirigido else grafo.vista_no_dirigida()
    base = len(componentes_conexas(g))
    criticos = {}
    for nodo in g.nodos:
        componentes = componentes_conexas(g, excluir=nodo)
        if len(componentes) > base:
            componentes.sort(key=len, reverse=True)
            separados = sorted(n for c in componentes[1:] for n in c)
            criticos[nodo] = separados
    return criticos


# --------------------------------------------------------------------- DFS
def dfs(grafo, inicio):
    """Orden de visita DFS recursivo desde ``inicio`` (como en la Guía 7)."""
    visitados = set()
    orden = []

    def visitar(nodo):
        visitados.add(nodo)
        orden.append(nodo)
        for vecino, _ in grafo.vecinos(nodo):
            if vecino not in visitados:
                visitar(vecino)

    visitar(inicio)
    return orden


def rastrear_caminos(grafo, origen, max_profundidad=6, max_caminos=500,
                     filtro=None):
    """Rastreo de fondos con DFS: todos los recorridos simples que parten de
    ``origen`` hasta un receptor final (sin salidas) o hasta la profundidad
    máxima. ``filtro(u, v, atributos)`` permite seguir solo ciertas aristas.
    Se usa una pila explícita para no depender de la recursión."""
    caminos = []
    pila = [(origen, [origen])]
    while pila and len(caminos) < max_caminos:
        nodo, camino = pila.pop()
        siguientes = [
            v for v, a in grafo.vecinos(nodo)
            if v not in camino and (filtro is None or filtro(nodo, v, a))
        ]
        if not siguientes or len(camino) - 1 >= max_profundidad:
            if len(camino) > 1:
                caminos.append(camino)
            continue
        for v in siguientes:
            pila.append((v, camino + [v]))
    return caminos


def caminos_simples(grafo, origen, destino, peso, max_saltos=6, k=None):
    """Enumera caminos simples origen -> destino con DFS, ordenados por costo.

    ``peso(u, v, atributos)`` da el costo de cada arista.
    Poda (ramificación y acotamiento): si ya se tienen ``k`` caminos y el costo
    parcial supera al peor de ellos, la rama se descarta. La poda solo es válida
    con pesos no negativos; si hay pesos negativos se desactiva.
    Devuelve lista de (costo, camino).
    """
    hay_negativos = any(peso(u, v, a) < 0 for u, v, a in grafo.aristas())
    resultados = []

    def peor_costo():
        return resultados[-1][0] if k is not None and len(resultados) >= k else None

    def visitar(nodo, camino, costo, en_camino):
        if nodo == destino:
            resultados.append((costo, list(camino)))
            resultados.sort(key=lambda r: r[0])
            if k is not None and len(resultados) > k:
                resultados.pop()
            return
        if len(camino) - 1 >= max_saltos:
            return
        for vecino, datos in grafo.vecinos(nodo):
            if vecino in en_camino:
                continue
            nuevo = costo + peso(nodo, vecino, datos)
            tope = peor_costo()
            if not hay_negativos and tope is not None and nuevo >= tope:
                continue
            camino.append(vecino)
            en_camino.add(vecino)
            visitar(vecino, camino, nuevo, en_camino)
            en_camino.discard(vecino)
            camino.pop()

    visitar(origen, [origen], 0, {origen})
    return resultados


def orden_topologico(grafo):
    """Orden topológico con DFS (Guía 7). Lanza ValueError si hay un ciclo,
    porque solo existe orden topológico en grafos dirigidos acíclicos."""
    estado = {}  # 1 = en proceso, 2 = terminado
    pila = []

    def visitar(nodo):
        estado[nodo] = 1
        for vecino, _ in grafo.vecinos(nodo):
            if estado.get(vecino) == 1:
                raise ValueError("El grafo tiene ciclos: no admite orden topológico.")
            if vecino not in estado:
                visitar(vecino)
        estado[nodo] = 2
        pila.append(nodo)

    for nodo in grafo.nodos:
        if nodo not in estado:
            visitar(nodo)
    return pila[::-1]


def capas_topologicas(dag):
    """Capa de cada nodo de un DAG = longitud del camino más largo desde una
    fuente. Se calcula recorriendo el orden topológico: O(V + E)."""
    capa = {n: 0 for n in dag.nodos}
    for u in orden_topologico(dag):
        for v, _ in dag.vecinos(u):
            capa[v] = max(capa[v], capa[u] + 1)
    return capa


# ------------------------------------------ componentes fuertemente conexas
def kosaraju(grafo):
    """Componentes fuertemente conexas con Kosaraju: dos pasadas DFS, la
    segunda sobre el grafo transpuesto en orden inverso de finalización."""
    visitados = set()
    finalizacion = []

    def dfs1(nodo):
        visitados.add(nodo)
        for vecino, _ in grafo.vecinos(nodo):
            if vecino not in visitados:
                dfs1(vecino)
        finalizacion.append(nodo)

    for nodo in grafo.nodos:
        if nodo not in visitados:
            dfs1(nodo)

    transpuesto = grafo.transpuesto()
    visitados.clear()
    componentes = []

    def dfs2(nodo, componente):
        visitados.add(nodo)
        componente.append(nodo)
        for vecino, _ in transpuesto.vecinos(nodo):
            if vecino not in visitados:
                dfs2(vecino, componente)

    for nodo in reversed(finalizacion):
        if nodo not in visitados:
            componente = []
            dfs2(nodo, componente)
            componentes.append(componente)
    return componentes


def tarjan(grafo):
    """Componentes fuertemente conexas con Tarjan: una sola pasada DFS usando
    índice de descubrimiento y lowlink."""
    indice = [0]
    pila = []
    en_pila = set()
    indices = {}
    lowlink = {}
    componentes = []

    def visitar(nodo):
        indices[nodo] = lowlink[nodo] = indice[0]
        indice[0] += 1
        pila.append(nodo)
        en_pila.add(nodo)
        for vecino, _ in grafo.vecinos(nodo):
            if vecino not in indices:
                visitar(vecino)
                lowlink[nodo] = min(lowlink[nodo], lowlink[vecino])
            elif vecino in en_pila:
                lowlink[nodo] = min(lowlink[nodo], indices[vecino])
        if lowlink[nodo] == indices[nodo]:
            componente = []
            while True:
                w = pila.pop()
                en_pila.discard(w)
                componente.append(w)
                if w == nodo:
                    break
            componentes.append(componente)

    for nodo in grafo.nodos:
        if nodo not in indices:
            visitar(nodo)
    return componentes


def ciclos_simples(grafo, nodos, max_longitud=8, max_ciclos=200):
    """Ciclos simples dentro de un conjunto de nodos (una componente fuerte),
    encontrados con DFS. Cada ciclo se reporta una sola vez, empezando por su
    nodo de menor orden."""
    permitidos = list(nodos)
    orden = {n: i for i, n in enumerate(sorted(permitidos))}
    ciclos = []

    for inicio in sorted(permitidos):
        pila = [(inicio, [inicio])]
        while pila and len(ciclos) < max_ciclos:
            nodo, camino = pila.pop()
            for vecino, _ in grafo.vecinos(nodo):
                if vecino == inicio and len(camino) > 1:
                    ciclos.append(camino + [inicio])
                elif (vecino in orden and orden[vecino] > orden[inicio]
                      and vecino not in camino and len(camino) < max_longitud):
                    pila.append((vecino, camino + [vecino]))
    return ciclos


def grafo_condensado(grafo, componentes, atributo_suma="monto_total"):
    """Grafo de componentes: cada componente fuerte se contrae en un nodo.
    El resultado siempre es acíclico (DAG). Devuelve (dag, mapa_nodo_comp)."""
    mapa = {}
    dag = Grafo(dirigido=True, ponderado=True, nombre="condensado")
    for i, comp in enumerate(componentes):
        dag.agregar_nodo(f"C{i}", miembros=len(comp))
        for n in comp:
            mapa[n] = f"C{i}"
    for u, v, datos in grafo.aristas():
        cu, cv = mapa[u], mapa[v]
        if cu == cv:
            continue
        valor = datos.get(atributo_suma, 1)
        if dag.existe_arista(cu, cv):
            dag.adyacencia[cu][cv][atributo_suma] += valor
        else:
            dag.agregar_arista(cu, cv, **{atributo_suma: valor})
    return dag, mapa


# ------------------------------------------------------------- bipartición
def es_bipartito(grafo):
    """Bipartición con BFS (coloreo en dos colores).
    Devuelve (es_bipartito, conjunto_A, conjunto_B, arista_conflicto)."""
    g = grafo if not grafo.dirigido else grafo.vista_no_dirigida()
    color = {}
    for inicio in g.nodos:
        if inicio in color:
            continue
        color[inicio] = 0
        cola = deque([inicio])
        while cola:
            nodo = cola.popleft()
            for vecino, _ in g.vecinos(nodo):
                if vecino not in color:
                    color[vecino] = 1 - color[nodo]
                    cola.append(vecino)
                elif color[vecino] == color[nodo]:
                    return False, set(), set(), (nodo, vecino)
    a = {n for n, c in color.items() if c == 0}
    b = {n for n, c in color.items() if c == 1}
    return True, a, b, None
