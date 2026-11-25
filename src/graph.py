"""Estructura de datos común del sistema: grafo con lista de adyacencia.

Todos los módulos (gestión, transacciones, enrutamiento, liquidez y evaluación)
trabajan sobre esta misma clase.

Representación
--------------
- ``nodos``:      {id_nodo: {atributo: valor}}
- ``adyacencia``: {id_nodo: {vecino: {atributo: valor}}}

Se usa lista de adyacencia (implementada con diccionarios) porque las redes
financieras son dispersas: el espacio es O(V + E) en lugar del O(V^2) de una
matriz. Usar un diccionario para los vecinos permite consultar, modificar o
eliminar una arista en O(1) promedio.

En un grafo no dirigido, la arista u-v se guarda en ambos sentidos y los dos
sentidos comparten el MISMO diccionario de atributos, por lo que modificar uno
modifica el otro.
"""

import math

# Atributos numéricos que pueden ser negativos (el resto debe ser >= 0).
ATRIBUTOS_NEGATIVOS_PERMITIDOS = {"bonificacion", "lat", "lon", "x", "y", "peso"}


class ErrorValidacion(ValueError):
    """Error lanzado cuando un dato viola las reglas de consistencia de la red."""


class Grafo:
    def __init__(self, dirigido=True, ponderado=True, nombre=""):
        self.dirigido = dirigido
        self.ponderado = ponderado
        self.nombre = nombre
        self.nodos = {}
        self.adyacencia = {}

    # ------------------------------------------------------------------ nodos
    def agregar_nodo(self, nodo, **atributos):
        nodo = self._normalizar_id(nodo)
        if nodo in self.nodos:
            raise ErrorValidacion(f"El nodo '{nodo}' ya existe.")
        self._validar_valores(atributos, f"nodo '{nodo}'")
        self.nodos[nodo] = dict(atributos)
        self.adyacencia[nodo] = {}
        return nodo

    def modificar_nodo(self, nodo, **atributos):
        self._exigir_nodo(nodo)
        self._validar_valores(atributos, f"nodo '{nodo}'")
        self.nodos[nodo].update(atributos)

    def eliminar_nodo(self, nodo):
        """Elimina el nodo y todas las aristas que entran o salen de él."""
        self._exigir_nodo(nodo)
        for vecinos in self.adyacencia.values():
            vecinos.pop(nodo, None)
        del self.adyacencia[nodo]
        del self.nodos[nodo]

    def existe_nodo(self, nodo):
        return nodo in self.nodos

    # ---------------------------------------------------------------- aristas
    def agregar_arista(self, origen, destino, **atributos):
        origen, destino = self._normalizar_id(origen), self._normalizar_id(destino)
        self._exigir_nodo(origen)
        self._exigir_nodo(destino)
        if origen == destino:
            raise ErrorValidacion(f"Lazo no permitido: '{origen}' -> '{destino}'.")
        if destino in self.adyacencia[origen]:
            raise ErrorValidacion(
                f"Conexión duplicada no justificada: '{origen}' -> '{destino}'."
            )
        if self.ponderado and not any(
            isinstance(v, (int, float)) for v in atributos.values()
        ):
            raise ErrorValidacion(
                f"La arista '{origen}' -> '{destino}' no tiene ningún peso numérico "
                "y el grafo es ponderado."
            )
        self._validar_valores(atributos, f"arista '{origen}' -> '{destino}'")
        datos = dict(atributos)
        self.adyacencia[origen][destino] = datos
        if not self.dirigido:
            self.adyacencia[destino][origen] = datos  # mismo objeto: simetría

    def modificar_arista(self, origen, destino, **atributos):
        self._exigir_arista(origen, destino)
        self._validar_valores(atributos, f"arista '{origen}' -> '{destino}'")
        self.adyacencia[origen][destino].update(atributos)

    def eliminar_arista(self, origen, destino):
        self._exigir_arista(origen, destino)
        del self.adyacencia[origen][destino]
        if not self.dirigido:
            del self.adyacencia[destino][origen]

    def existe_arista(self, origen, destino):
        return origen in self.adyacencia and destino in self.adyacencia[origen]

    def atributos_arista(self, origen, destino):
        self._exigir_arista(origen, destino)
        return self.adyacencia[origen][destino]

    # -------------------------------------------------------------- consultas
    def vecinos(self, nodo):
        """Pares (vecino, atributos) de las aristas que salen de ``nodo``."""
        return self.adyacencia[nodo].items()

    def peso(self, origen, destino, atributo="peso"):
        """Peso de una arista según un atributo. En grafos no ponderados vale 1."""
        if not self.ponderado:
            return 1
        return self.adyacencia[origen][destino].get(atributo, 1)

    def aristas(self):
        """Lista de aristas (origen, destino, atributos).

        En un grafo no dirigido cada arista aparece una sola vez.
        """
        resultado = []
        vistas = set()
        for u, vecinos in self.adyacencia.items():
            for v, datos in vecinos.items():
                if not self.dirigido:
                    clave = frozenset((u, v))
                    if clave in vistas:
                        continue
                    vistas.add(clave)
                resultado.append((u, v, datos))
        return resultado

    def numero_nodos(self):
        return len(self.nodos)

    def numero_aristas(self):
        total = sum(len(v) for v in self.adyacencia.values())
        return total if self.dirigido else total // 2

    def grado_salida(self, nodo):
        return len(self.adyacencia[nodo])

    def grado_entrada(self, nodo):
        if not self.dirigido:
            return len(self.adyacencia[nodo])
        return sum(1 for vecinos in self.adyacencia.values() if nodo in vecinos)

    def nodos_por_tipo(self, tipo):
        return [n for n, a in self.nodos.items() if a.get("tipo") == tipo]

    # ---------------------------------------------------------- derivaciones
    def copiar(self):
        nuevo = Grafo(self.dirigido, self.ponderado, self.nombre)
        for n, a in self.nodos.items():
            nuevo.nodos[n] = dict(a)
            nuevo.adyacencia[n] = {}
        for u, v, datos in self.aristas():
            nuevo.agregar_arista(u, v, **datos)
        return nuevo

    def transpuesto(self):
        """Grafo con todas las aristas invertidas (usado por Kosaraju)."""
        if not self.dirigido:
            return self.copiar()
        nuevo = Grafo(True, self.ponderado, self.nombre + " (transpuesto)")
        for n, a in self.nodos.items():
            nuevo.nodos[n] = dict(a)
            nuevo.adyacencia[n] = {}
        for u, v, datos in self.aristas():
            nuevo.adyacencia[v][u] = dict(datos)
        return nuevo

    def filtrar_aristas(self, predicado):
        """Nuevo grafo con los mismos nodos y solo las aristas que cumplen
        ``predicado(origen, destino, atributos)``."""
        nuevo = Grafo(self.dirigido, self.ponderado, self.nombre)
        for n, a in self.nodos.items():
            nuevo.nodos[n] = dict(a)
            nuevo.adyacencia[n] = {}
        for u, v, datos in self.aristas():
            if predicado(u, v, datos):
                nuevo.agregar_arista(u, v, **datos)
        return nuevo

    def vista_no_dirigida(self):
        """Versión no dirigida (relación sin importar el sentido)."""
        nuevo = Grafo(False, self.ponderado, self.nombre + " (no dirigido)")
        for n, a in self.nodos.items():
            nuevo.nodos[n] = dict(a)
            nuevo.adyacencia[n] = {}
        for u, v, datos in self.aristas():
            if not nuevo.existe_arista(u, v):
                nuevo.adyacencia[u][v] = datos
                nuevo.adyacencia[v][u] = datos
        return nuevo

    def lista_adyacencia(self, atributo="peso"):
        """Formato de las guías: {"A": [("B", 4.5), ("C", 2.0)], ...}."""
        return {
            u: [(v, self.peso(u, v, atributo)) for v in vecinos]
            for u, vecinos in self.adyacencia.items()
        }

    def matriz_adyacencia(self, atributo="peso"):
        """Devuelve (orden_de_nodos, matriz) con 0 en la diagonal e inf donde
        no hay arista. Se usa solo cuando el algoritmo lo exige (Floyd-Warshall)."""
        orden = list(self.nodos)
        indice = {n: i for i, n in enumerate(orden)}
        n = len(orden)
        matriz = [[math.inf] * n for _ in range(n)]
        for i in range(n):
            matriz[i][i] = 0
        for u, vecinos in self.adyacencia.items():
            for v in vecinos:
                matriz[indice[u]][indice[v]] = self.peso(u, v, atributo)
        return orden, matriz

    # ------------------------------------------------------------ validación
    def validar(self):
        """Revisa la consistencia interna y devuelve la lista de problemas."""
        problemas = []
        for u, vecinos in self.adyacencia.items():
            if u not in self.nodos:
                problemas.append(f"'{u}' tiene aristas pero no está registrado como nodo.")
            for v, datos in vecinos.items():
                if v not in self.nodos:
                    problemas.append(f"Arista '{u}' -> '{v}' apunta a un nodo inexistente.")
                if not self.dirigido and self.adyacencia.get(v, {}).get(u) is not datos:
                    problemas.append(f"Arista no dirigida '{u}' - '{v}' no es simétrica.")
                try:
                    self._validar_valores(datos, f"arista '{u}' -> '{v}'")
                except ErrorValidacion as e:
                    problemas.append(str(e))
        for n in self.nodos:
            if n not in self.adyacencia:
                problemas.append(f"El nodo '{n}' no tiene lista de adyacencia.")
        return problemas

    # ---------------------------------------------------------------- apoyo
    @staticmethod
    def _normalizar_id(nodo):
        nodo = str(nodo).strip()
        if not nodo:
            raise ErrorValidacion("El identificador de un nodo no puede estar vacío.")
        return nodo

    @staticmethod
    def _validar_valores(atributos, contexto):
        for clave, valor in atributos.items():
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                continue
            if math.isnan(valor):
                raise ErrorValidacion(f"Valor no numérico en '{clave}' de {contexto}.")
            if valor < 0 and clave not in ATRIBUTOS_NEGATIVOS_PERMITIDOS:
                raise ErrorValidacion(
                    f"Valor negativo inválido en '{clave}' = {valor} de {contexto}."
                )

    def _exigir_nodo(self, nodo):
        if nodo not in self.nodos:
            raise ErrorValidacion(f"El nodo '{nodo}' no existe.")

    def _exigir_arista(self, origen, destino):
        if not self.existe_arista(origen, destino):
            raise ErrorValidacion(f"La arista '{origen}' -> '{destino}' no existe.")

    def __contains__(self, nodo):
        return nodo in self.nodos

    def __len__(self):
        return len(self.nodos)

    def __repr__(self):
        tipo = "dirigido" if self.dirigido else "no dirigido"
        pond = "ponderado" if self.ponderado else "no ponderado"
        return (f"Grafo('{self.nombre}', {tipo}, {pond}, "
                f"V={self.numero_nodos()}, E={self.numero_aristas()})")
