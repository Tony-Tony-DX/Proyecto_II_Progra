"""Guía 8 – Árboles de expansión mínima: Kruskal y Prim.

Ambos son algoritmos voraces y requieren un grafo no dirigido y ponderado.
Si el grafo no es conexo, devuelven un bosque de expansión mínima (un árbol
por componente).

- Kruskal: O(E log E)  (ordenar aristas + Union-Find)
- Prim:    O(E log V)  (cola de prioridad con heapq)
"""

import heapq


class UnionFind:
    """Conjuntos disjuntos con compresión de caminos y unión por rango."""

    def __init__(self, elementos):
        self.padre = {e: e for e in elementos}
        self.rango = {e: 0 for e in elementos}

    def find(self, x):
        if self.padre[x] != x:
            self.padre[x] = self.find(self.padre[x])
        return self.padre[x]

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False  # ya estaban conectados: la arista formaría ciclo
        if self.rango[ra] < self.rango[rb]:
            ra, rb = rb, ra
        self.padre[rb] = ra
        if self.rango[ra] == self.rango[rb]:
            self.rango[ra] += 1
        return True


def _exigir_no_dirigido(grafo):
    if grafo.dirigido:
        raise ValueError("El árbol de expansión mínima requiere un grafo no dirigido.")


def kruskal(grafo, atributo="peso", traza=None):
    """Devuelve (aristas_del_arbol, costo_total).
    Cada arista es una tupla (u, v, peso). ``traza`` registra cada arista
    aceptada o rechazada (por formar ciclo)."""
    _exigir_no_dirigido(grafo)
    aristas = sorted(
        ((grafo.peso(u, v, atributo), u, v) for u, v, _ in grafo.aristas()),
        key=lambda t: t[0],
    )
    uf = UnionFind(grafo.nodos)
    arbol = []
    costo = 0
    for peso, u, v in aristas:
        if uf.union(u, v):
            arbol.append((u, v, peso))
            costo += peso
            if traza is not None:
                traza.append({"tipo": "aceptar", "u": u, "v": v, "peso": peso, "costo": costo})
            if len(arbol) == grafo.numero_nodos() - 1:
                break
        elif traza is not None:
            traza.append({"tipo": "rechazar", "u": u, "v": v, "peso": peso, "costo": costo})
    return arbol, costo


def prim(grafo, atributo="peso", inicio=None):
    """Devuelve (aristas_del_arbol, costo_total). Si el grafo no es conexo,
    reinicia desde un nodo no visitado y produce un bosque."""
    _exigir_no_dirigido(grafo)
    visitados = set()
    arbol = []
    costo = 0
    pendientes = list(grafo.nodos)
    if inicio is not None:
        pendientes.remove(inicio)
        pendientes.insert(0, inicio)

    for raiz in pendientes:
        if raiz in visitados:
            continue
        visitados.add(raiz)
        cola = [(grafo.peso(raiz, v, atributo), raiz, v) for v, _ in grafo.vecinos(raiz)]
        heapq.heapify(cola)
        while cola:
            peso, u, v = heapq.heappop(cola)
            if v in visitados:
                continue
            visitados.add(v)
            arbol.append((u, v, peso))
            costo += peso
            for w, _ in grafo.vecinos(v):
                if w not in visitados:
                    heapq.heappush(cola, (grafo.peso(v, w, atributo), v, w))
    return arbol, costo
