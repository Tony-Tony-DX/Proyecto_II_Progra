"""Guía 11 – Flujo máximo: Ford-Fulkerson, Edmonds-Karp y corte mínimo.

La red se guarda como lista de arcos con su arco inverso (red residual):
cada arco original u -> v con capacidad c crea además un arco v -> u con
capacidad 0. Enviar f unidades por u -> v resta f a su capacidad residual y
suma f a la del inverso, lo que permite "deshacer" flujo en iteraciones
posteriores. Esta representación admite arcos antiparalelos (carreteras de
doble sentido) sin ambigüedad.

Complejidades (V nodos, E arcos, |f*| valor del flujo máximo, F aumentos):
- Ford-Fulkerson con DFS:   O(E · |f*|)
- Edmonds-Karp (BFS):       O(V · E^2)
- Corte mínimo:             O(V + E) después del flujo máximo
- Ford-Fulkerson con caminos de menor costo (Bellman-Ford): O(F · V · E)
"""

import math
from collections import deque


class RedFlujo:
    def __init__(self):
        self.arcos = {}  # nodo -> lista de índices de arcos que salen de él
        # Cada arco: [destino, capacidad_residual, costo, indice_inverso,
        #             capacidad_original, es_original]
        self.lista = []

    def agregar_nodo(self, nodo):
        self.arcos.setdefault(nodo, [])

    def agregar_arco(self, u, v, capacidad, costo=0):
        """Agrega el arco u -> v y su inverso. Devuelve el índice del arco."""
        if capacidad < 0:
            raise ValueError(f"Capacidad negativa en {u} -> {v}.")
        self.agregar_nodo(u)
        self.agregar_nodo(v)
        i = len(self.lista)
        self.lista.append([v, capacidad, costo, i + 1, capacidad, True])
        self.lista.append([u, 0, -costo, i, 0, False])
        self.arcos[u].append(i)
        self.arcos[v].append(i + 1)
        return i

    def origen_de(self, indice):
        return self.lista[self.lista[indice][3]][0]

    def flujo_arco(self, indice):
        arco = self.lista[indice]
        return arco[4] - arco[1]

    def arcos_originales(self):
        """Lista de (indice, u, v, capacidad, flujo, costo)."""
        resultado = []
        for i, arco in enumerate(self.lista):
            if arco[5]:
                resultado.append((i, self.origen_de(i), arco[0], arco[4],
                                  arco[4] - arco[1], arco[2]))
        return resultado

    def reiniciar(self):
        for arco in self.lista:
            arco[1] = arco[4]

    def numero_nodos(self):
        return len(self.arcos)

    def numero_arcos(self):
        return len(self.lista) // 2

    def _aumentar(self, camino_arcos, cantidad):
        for i in camino_arcos:
            self.lista[i][1] -= cantidad
            self.lista[self.lista[i][3]][1] += cantidad


def _reconstruir(red, padre_arco, s, t):
    """Lista de índices de arcos desde s hasta t usando el arco padre."""
    arcos = []
    nodo = t
    while nodo != s:
        indice = padre_arco[nodo]
        arcos.append(indice)
        nodo = red.origen_de(indice)
    return arcos[::-1]


def _cuello_de_botella(red, arcos):
    return min(red.lista[i][1] for i in arcos)


# ---------------------------------------------------- Ford-Fulkerson (DFS)
def ford_fulkerson(red, s, t):
    """Ford-Fulkerson básico: busca caminos aumentantes con DFS (pila).
    Devuelve (valor_flujo, numero_de_aumentos)."""
    red.reiniciar()
    total = 0
    aumentos = 0
    while True:
        padre = {s: None}
        pila = [s]
        while pila and t not in padre:
            u = pila.pop()
            for i in red.arcos[u]:
                v, residual = red.lista[i][0], red.lista[i][1]
                if residual > 0 and v not in padre:
                    padre[v] = i
                    pila.append(v)
        if t not in padre:
            break
        camino = _reconstruir(red, padre, s, t)
        cantidad = _cuello_de_botella(red, camino)
        red._aumentar(camino, cantidad)
        total += cantidad
        aumentos += 1
    return total, aumentos


# -------------------------------------------------------------- Edmonds-Karp
def edmonds_karp(red, s, t, traza=None):
    """Ford-Fulkerson con BFS: siempre aumenta por el camino con menos arcos.
    Devuelve (valor_flujo, numero_de_aumentos). ``traza`` registra cada camino
    aumentante con su cuello de botella."""
    red.reiniciar()
    total = 0
    aumentos = 0
    while True:
        padre = {s: None}
        cola = deque([s])
        while cola and t not in padre:
            u = cola.popleft()
            for i in red.arcos[u]:
                v, residual = red.lista[i][0], red.lista[i][1]
                if residual > 0 and v not in padre:
                    padre[v] = i
                    cola.append(v)
        if t not in padre:
            break
        camino = _reconstruir(red, padre, s, t)
        cantidad = _cuello_de_botella(red, camino)
        red._aumentar(camino, cantidad)
        total += cantidad
        aumentos += 1
        if traza is not None:
            nodos = [s] + [red.lista[i][0] for i in camino]
            traza.append({"tipo": "aumentar", "camino": nodos, "cantidad": cantidad,
                          "total": total})
    return total, aumentos


# -------------------------------------------------------------- Corte mínimo
def corte_minimo(red, s):
    """Después de calcular el flujo máximo: S = nodos alcanzables desde s en la
    red residual (BFS). Las aristas originales S -> T forman el corte mínimo.
    Devuelve (S, aristas_corte, capacidad_corte)."""
    alcanzables = {s}
    cola = deque([s])
    while cola:
        u = cola.popleft()
        for i in red.arcos[u]:
            v, residual = red.lista[i][0], red.lista[i][1]
            if residual > 0 and v not in alcanzables:
                alcanzables.add(v)
                cola.append(v)
    corte = []
    capacidad = 0
    for i, u, v, cap, flujo, _ in red.arcos_originales():
        if u in alcanzables and v not in alcanzables and cap > 0:
            corte.append((u, v, cap))
            capacidad += cap
    return alcanzables, corte, capacidad


# ------------------------- Ford-Fulkerson con caminos aumentantes de menor costo
def ford_fulkerson_costo_minimo(red, s, t):
    """Variante de Ford-Fulkerson (Guía 11) en la que cada camino aumentante
    es el de MENOR COSTO en la red residual, hallado con Bellman-Ford (Guía 9).

    Se necesita Bellman-Ford y no Dijkstra porque los arcos inversos de la red
    residual tienen costo negativo (deshacer un envío devuelve su costo).
    Al aumentar siempre por el camino más barato, el resultado es el flujo
    máximo con el menor costo total.
    Devuelve (valor_flujo, costo_total, numero_de_aumentos)."""
    red.reiniciar()
    total = 0
    costo_total = 0
    aumentos = 0
    nodos = list(red.arcos)
    while True:
        dist = {n: math.inf for n in nodos}
        padre = {s: None}
        dist[s] = 0
        for _ in range(len(nodos) - 1):
            cambio = False
            for u in nodos:
                if dist[u] == math.inf:
                    continue
                for i in red.arcos[u]:
                    v, residual, costo = red.lista[i][0], red.lista[i][1], red.lista[i][2]
                    if residual > 0 and dist[u] + costo < dist[v]:
                        dist[v] = dist[u] + costo
                        padre[v] = i
                        cambio = True
            if not cambio:
                break
        if dist[t] == math.inf:
            break
        camino = _reconstruir(red, padre, s, t)
        cantidad = _cuello_de_botella(red, camino)
        red._aumentar(camino, cantidad)
        total += cantidad
        costo_total += cantidad * dist[t]
        aumentos += 1
    return total, costo_total, aumentos


def verificar_flujo(red, s, t):
    """Comprueba restricción de capacidad y conservación de flujo.
    Devuelve la lista de violaciones (vacía si el flujo es válido)."""
    problemas = []
    balance = {n: 0 for n in red.arcos}
    for _, u, v, cap, flujo, _ in red.arcos_originales():
        if flujo < 0 or flujo > cap:
            problemas.append(f"Capacidad violada en {u} -> {v}: flujo {flujo}, capacidad {cap}")
        balance[u] -= flujo
        balance[v] += flujo
    for n, b in balance.items():
        if n not in (s, t) and abs(b) > 1e-9:
            problemas.append(f"No se conserva el flujo en {n}: balance {b}")
    if abs(balance[s] + balance[t]) > 1e-9:
        problemas.append("Lo que sale de la fuente no coincide con lo que llega al sumidero")
    return problemas
