# Sistema de Análisis y Optimización de Redes Financieras

**Proyecto II – Programación III** · Caso de estudio: **Caja Municipal Andina** (entidad ficticia), departamento de Cusco.

Sistema en Python que modela la red operativa de una caja municipal mediante grafos y resuelve tres escenarios:

1. **Prevención de fraudes y lavado de activos**: pitufeo, ciclos de fondos, cuentas puente, estratificación y viaje imposible de tarjetas.
2. **Enrutamiento de operaciones y cálculo de comisiones**: transferencias interplaza e interbancarias, billeteras, tarjetas y cajeros.
3. **Distribución de liquidez hacia bóvedas y agencias**: temporada normal, temporada alta (Inti Raymi) y un huaico en Abra Málaga.

Todos los algoritmos provienen de las **guías de laboratorio 7 a 11** del curso y están implementados a mano en `src/algoritmos/`. El planteamiento completo está en [`docs/Problematica_Caja_Municipal_Andina_v2.pdf`](docs/Problematica_Caja_Municipal_Andina_v2.pdf).

> **Aviso:** la entidad, sus clientes, transacciones, comisiones y capacidades son **datos simulados**. Los patrones detectados son **indicadores para revisión**: no prueban la existencia de fraude ni de lavado de activos.

---

## 1. Requisitos e instalación

**Requisitos:**

- **Python 3.9 o superior.** Se probó con una instalación limpia en Python 3.9.13 y en Python 3.15.0, ambos en Windows 11. Si no tiene Python, descárguelo de [python.org](https://www.python.org/downloads/) y, en Windows, marque la casilla **“Add python.exe to PATH”** durante la instalación.
- **Un navegador** (Chrome, Edge o Firefox).
- **Internet**, solo para instalar las dependencias la primera vez. Después, todo funciona sin conexión.
- **Dependencias:** `matplotlib`, solo para las imágenes PNG de los reportes, y `pytest`, para las pruebas. Los algoritmos usan únicamente la biblioteca estándar (`heapq`, `collections`, `math`).

### Paso 1 · Obtener el proyecto

Elija una de las dos formas:

- **Con git:**
  ```bash
  git clone <URL-del-repositorio>
  ```
- **Sin git:** en GitHub, use **Code → Download ZIP** y descomprima el archivo.

Luego abra una terminal **dentro de la carpeta del proyecto**, la que contiene `main.py`. En Windows: abra la carpeta en el Explorador, escriba `cmd` en la barra de direcciones y presione Enter.

### Paso 2 · Instalar las dependencias

```bash
python -m pip install -r requirements.txt
```

### Paso 3 · Ejecutar

```bash
python main.py
```

El navegador se abre solo con la interfaz. Si no se abre, copie en el navegador la dirección que aparece en la terminal (normalmente `http://127.0.0.1:8050/`). Para cerrar el programa, presione `Ctrl+C` en la terminal.

### Opcional · Entorno virtual

Es recomendable para no mezclar estas bibliotecas con otros proyectos:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt    # Windows
.venv\Scripts\python main.py
# Linux/macOS: .venv/bin/python -m pip install -r requirements.txt  y  .venv/bin/python main.py
```

### Problemas frecuentes

| Problema | Solución |
|---|---|
| `python` no se reconoce como comando (Windows) | Use `py` en lugar de `python` (por ejemplo, `py main.py`), o reinstale Python marcando “Add python.exe to PATH”. |
| `pip` no se reconoce | Use siempre `python -m pip …`, como en el paso 2. |
| PowerShell no deja activar el entorno virtual | No hace falta activarlo: use `.venv\Scripts\python main.py`, como en la sección opcional. |
| El puerto 8050 está ocupado | El programa usa automáticamente el siguiente libre (8051, 8052…) y lo indica en la terminal. |
| No se instaló `matplotlib` | La interfaz gráfica igual funciona; solo fallan las imágenes PNG de `--reportes`. |

## 2. Ejecución

| Comando | Qué hace |
|---|---|
| `python main.py` | Abre la **interfaz gráfica** en el navegador (http://127.0.0.1:8050) |
| `python main.py --sin-navegador` | Inicia la interfaz sin abrir el navegador automáticamente |
| `python main.py --terminal` | Abre el menú interactivo de terminal con los 5 módulos |
| `python main.py --reportes` | Genera todos los reportes en `reportes/` sin preguntar nada |
| `python main.py --datos` | Regenera los datos simulados (semilla 2026) |
| `python -m pytest` | Ejecuta las 77 pruebas automatizadas |

### Interfaz gráfica

Es una aplicación web **local**: el servidor usa solo la biblioteca estándar (`http.server`) y la página no carga nada de internet, así que funciona sin conexión durante la exposición. Para detener el servidor se presiona `Ctrl+C` en la terminal.

| Sección | Qué se puede hacer |
|---|---|
| **Inicio** | Indicadores generales y un **guion de exposición** de 8 pasos; cada paso lleva directo a la demostración |
| **1 · Gestión de la red** | Mapa interactivo de Cusco, agregar/modificar/eliminar nodos y tramos con validación en vivo, cargar CSV/TXT/JSON, puntos críticos, titularidad bipartita |
| **2 · Fraude y lavado** | Una pestaña por patrón con su grafo (estrella, ciclo, capas), viaje imposible sobre el mapa, proximidad BFS en anillos, rastreo DFS, Kosaraju vs Tarjan |
| **3 · Enrutamiento** | Escenarios de Cusco, deslizador de monto, rutas más barata y más rápida resaltadas, alternativas, campañas de cashback y ruleteo, matriz de tiempos (Floyd-Warshall / Johnson) |
| **4 · Liquidez** | Flujo animado sobre el mapa, temporada, método, filtro de riesgo por lluvias, **clic en un tramo para cerrarlo**, botón de huaico, corte mínimo, red troncal y puntos críticos |
| **5 · Evaluación** | Validación 21/21, comparación de algoritmos con gráficas, huaico antes/después |
| **Algoritmos en acción** | Animación **paso a paso** de BFS, Dijkstra, Kruskal, Edmonds-Karp y Floyd-Warshall, con pseudocódigo resaltado y estado (cola, distancias, matriz). Se puede usar el ejemplo de la guía o la red de Cusco. Teclas: ← → y espacio |
| **Sustentación** | Tabla de justificación de algoritmos, decisiones de modelado y preguntas frecuentes del jurado |
| **Reportes** | Generar y descargar todos los reportes; abrir el PDF de la problemática |

Botones de la barra superior: **Modo exposición** (letra más grande para proyectar), **Pantalla completa** y **Tema** claro/oscuro.

Menú de la terminal (`python main.py --terminal`):

```
1. Gestión y modelamiento de la red      -> resumen, validación, CRUD de nodos y aristas, carga CSV/TXT/JSON, mapa PNG
2. Análisis de transacciones             -> reporte de patrones sospechosos, rastreo DFS, proximidad BFS, Kosaraju vs Tarjan
3. Enrutamiento y comisiones             -> escenarios de Cusco, consulta personalizada, cashback y ruleteo, matriz de tiempos
4. Distribución de liquidez              -> plan normal, alta, alta con huaico; red troncal y puntos críticos
5. Evaluación y validación               -> casos con resultado esperado, comparación de algoritmos, escenario huaico
6. Generar todos los reportes
```

## 3. Estructura del proyecto

```
PROYECTO_PROGRAIII/
├── main.py                      punto de entrada (interfaz gráfica o terminal)
├── requirements.txt / pytest.ini / .gitignore
├── data/                        datos simulados (ver sección 5)
├── src/
│   ├── graph.py                 estructura común: grafo con lista de adyacencia
│   ├── algoritmos/
│   │   ├── recorridos.py        Guía 7: BFS, DFS, orden topológico, Kosaraju, Tarjan, bipartición
│   │   ├── arbol_expansion.py   Guía 8: Kruskal (Union-Find), Prim
│   │   ├── rutas_cortas.py      Guías 9 y 10: Dijkstra, Bellman-Ford, Johnson, Floyd-Warshall
│   │   └── flujo.py             Guía 11: Ford-Fulkerson, Edmonds-Karp, corte mínimo
│   ├── gestion_red.py           Módulo 1
│   ├── analisis_transacciones.py Módulo 2
│   ├── enrutamiento_financiero.py Módulo 3
│   ├── distribucion_liquidez.py Módulo 4
│   ├── evaluacion_resultados.py Módulo 5
│   ├── generador_datos.py       generador reproducible de transacciones
│   ├── utils.py                 CSV, tablas, medición de tiempo y memoria
│   └── interfaz/
│       ├── servidor.py          servidor web local (http.server)
│       ├── api.py               servicios JSON que llaman a los módulos 1 a 5
│       └── web/                 index.html, estilos.css, graficos.js (SVG propio), app.js
├── tests/                       pruebas con pytest (una por módulo + interfaz)
├── docs/                        problemática (PDF y fuente HTML)
└── reportes/                    salidas generadas (no se versiona)
```

## 4. Representación común del grafo

`src/graph.py` define la clase `Grafo`, que usan todos los módulos:

- **Lista de adyacencia con diccionarios**: `adyacencia[u][v] = {atributos}`. Ocupa O(V + E) y las redes de la caja son dispersas. La matriz de adyacencia solo se construye cuando un algoritmo la necesita (Floyd-Warshall).
- Admite grafos **dirigidos y no dirigidos, ponderados y no ponderados**. En un grafo no dirigido los dos sentidos comparten el mismo diccionario de atributos.
- **Validación** al crear o modificar: rechaza nodos inexistentes, conexiones duplicadas no justificadas, lazos, valores negativos o no numéricos (salvo atributos permitidos, como `bonificacion`) y grafos ponderados sin peso numérico.

| Red | Tipo | Archivo |
|---|---|---|
| Red física (carreteras y tren) | no dirigida, ponderada | `nodos.csv` + `rutas_fisicas.csv` |
| Red de liquidez | dirigida, ponderada | `nodos.csv` + `distribucion_liquidez.csv` |
| Canales de operación | dirigida, ponderada | `nodos_enrutamiento.csv` + `red_enrutamiento*.csv` |
| Transacciones entre cuentas | dirigida, ponderada | `transacciones.csv` |
| Titularidad cliente – cuenta | no dirigida, no ponderada (bipartita) | `titularidad.csv` |

## 5. Datos simulados (`data/`)

| Archivo | Contenido | Tamaño |
|---|---|---|
| `nodos.csv` | id, nombre, tipo, provincia, lat, lon, oferta, almacenamiento, demanda_normal, demanda_alta (miles de S/) | 39 nodos |
| `rutas_fisicas.csv` | origen, destino, tipo_via, distancia_km, tiempo_h, riesgo (1–10), nombre | 40 tramos |
| `distribucion_liquidez.csv` | origen, destino, capacidad (miles de S/ por día), costo_unitario, tiempo_h, riesgo, sentido (`doble` o `ida`) | 40 rutas |
| `nodos_enrutamiento.csv` | id, nombre, tipo de cada cuenta, canal o entidad | 22 nodos |
| `red_enrutamiento.csv` | origen, destino, canal, comision_fija, comision_pct, bonificacion, tiempo_min, limite, disponible | 32 canales |
| `red_enrutamiento_promo.csv` | campaña con cashback, que produce pesos negativos | 1 cambio |
| `red_enrutamiento_ruleteo.csv` | cashback más devolución a la cuenta, que produce un ciclo negativo | 2 cambios |
| `titularidad.csv` | cliente, cuenta, tipo_cliente, agencia | 426 cuentas |
| `transacciones.csv` | id, origen, destino, monto, fecha_hora, canal, agencia (junio 2026) | 5 047 operaciones |
| `retiros_atm.csv` | id, tarjeta, cajero, fecha_hora, monto | 759 retiros |
| `patrones_esperados.json` | patrones insertados a propósito (resultado esperado de las pruebas) | — |

**Cómo se construyeron los datos:**

- La red física y la de liquidez se escribieron a mano sobre la geografía real de Cusco: Abra Málaga, el tren a Machupicchu y la Interoceánica.
- Las transacciones, la titularidad y los retiros los genera `src/generador_datos.py` con la **semilla 2026**, así que cualquier persona obtiene exactamente los mismos archivos.
- El tráfico normal no tiene ciclos: personas → comercios → mayoristas, más transferencias entre personas en un solo sentido. Así, los patrones insertados son el resultado esperado y conocido.

## 6. Módulos y algoritmos

| Módulo | Necesidad | Algoritmo (guía) | Complejidad |
|---|---|---|---|
| M1 | Conectividad y validación | BFS; bipartición (G7) | O(V+E) |
| M2 | Proximidad a cuentas marcadas | BFS por niveles (G7) | O(V+E) |
| M2 | Rastreo de fondos y ciclos | DFS (G7) | O(V+E) por recorrido |
| M2 | Grupos de cuentas | Tarjan y Kosaraju (G7) | O(V+E) |
| M2 | Estratificación | Orden topológico del grafo condensado (G7) | O(V+E) |
| M2 | Viaje imposible | Tiempos mínimos con Floyd-Warshall (G10) | O(V³) |
| M3 | Ruta de menor comisión o tiempo | Dijkstra con heapq (G9) | O((V+E) log V) |
| M3 | Bonificaciones y ruleteo | Bellman-Ford (G9) | O(V·E) |
| M3 | Rutas alternativas | Enumeración DFS con poda (G7) | exponencial, acotada |
| M3 | Matriz de tiempos entre ciudades | Floyd-Warshall (G10) / Johnson (G9) | O(V³) / O(V·E log V) |
| M4 | Efectivo máximo distribuible | Edmonds-Karp (G11) | O(V·E²) |
| M4 | Cuellos de botella | Corte mínimo (G11) | O(V+E) |
| M4 | Distribución al menor costo | Ford-Fulkerson con caminos de menor costo hallados con Bellman-Ford (G11 + G9) | O(F·V·E) |
| M4 | Red troncal de menor riesgo | Kruskal y Prim (G8) | O(E log E) / O(E log V) |
| M4 | Puntos críticos | Eliminación de nodos + BFS (G7) | O(V·(V+E)) |
| M5 | Comparación empírica | Dijkstra vs Bellman-Ford, Floyd-Warshall vs Johnson, Kosaraju vs Tarjan, Kruskal vs Prim, Ford-Fulkerson vs Edmonds-Karp | — |

**Decisiones de modelado:**

- **Comisiones.** Se cobran aparte al ordenante, así que el peso de cada canal es `comision_fija + comision_pct/100 × monto − bonificacion`, calculado para el monto de cada consulta.
- **Restricciones.** Los canales no disponibles o con límite menor que el monto se excluyen antes de buscar la ruta.
- **Flujo.** Se usa una súper-fuente con la oferta de cada bóveda y un súper-sumidero con la demanda de cada punto de atención. Cada bóveda regional se divide en `v::entrada → v::salida`, con capacidad igual a su almacenamiento. Cada ruta de doble sentido se modela como dos arcos.
- **Por qué Bellman-Ford en el flujo de costo mínimo.** La red residual tiene arcos inversos de costo negativo, y con pesos negativos Dijkstra no es correcto.

## 7. Resultados principales (datos con semilla 2026)

- **M2:** detecta los 5 patrones insertados sin falsos positivos:
  - pitufeo hacia `E_ORO01`: 18 depósitos de 8 cuentas en 48 h;
  - ciclo `E_COM1→E_COM2→E_COM3→E_COM4→E_COM1`;
  - cuenta puente `B_PUENTE01`: reenvía el 97 % en 4,5 h;
  - estratificación en 3 capas hasta `LY_FINAL`;
  - viaje imposible de las tarjetas `T9001` y `T9002` (el turista legítimo `T0250` no se marca).
- **M3:** para S/ 5 000 de Quillabamba a Lima:
  - la ruta más barata es la transferencia diferida (S/ 3,50, 24 h);
  - la más rápida es la inmediata (S/ 8,00, 2 min);
  - para S/ 1 500 conviene la billetera (S/ 2,25);
  - con la campaña de cashback se usa Bellman-Ford, y en la variante de ruleteo detecta un ciclo negativo de S/ −3 por vuelta.
- **M4, temporada normal:** se cubre el 100 % de la demanda.
- **M4, temporada alta:**
  - se cubre el 97,6 % de la demanda;
  - el corte mínimo son los dos tramos de tren hacia Machupicchu Pueblo (700 + 400);
  - el plan de costo mínimo cuesta S/ 80 280 mil, frente a S/ 80 720 mil del plan de Ford-Fulkerson con DFS, y distribuye la misma cantidad. En esta red, Edmonds-Karp coincide por casualidad con el costo óptimo, pero no lo garantiza.
- **Huaico en Abra Málaga:**
  - la demanda no cubierta sube de S/ 400 mil a S/ 1 210 mil;
  - Quillabamba y Echarati quedan desabastecidos;
  - el tiempo Cusco → Quillabamba pasa de 6,4 h a 7,5 h;
  - la Hidroeléctrica y Santa Teresa pasan a ser puntos críticos.
- **M5:**
  - las 21 validaciones de escenarios son correctas;
  - en las redes sintéticas, cada par de algoritmos da el mismo resultado;
  - Floyd-Warshall supera a Johnson en redes pequeñas, y Johnson gana desde unos 150 nodos;
  - Edmonds-Karp necesita entre 2 y 12 veces menos aumentos que Ford-Fulkerson con DFS.

Los valores exactos de tiempo y memoria dependen de la máquina; las cantidades, rutas y patrones son idénticos en cualquier equipo.

## 8. Pruebas y reproducibilidad

```bash
python -m pytest            # 77 pruebas
python main.py --reportes   # regenera todos los reportes del informe en reportes/
```

Las pruebas cubren:

- los ejemplos resueltos de las guías: Dijkstra A→E = 5 (G9), Floyd-Warshall A→X = 8 (G10), el MST de la red hidráulica con costo 10 (G8) y el flujo máximo de la red clásica = 23 (G11);
- las validaciones de datos;
- los patrones insertados;
- los escenarios de Cusco;
- la coincidencia entre algoritmos alternativos.

## 9. Limitaciones

- La red física está simplificada y las capacidades de transporte y comisiones son supuestos.
- El tráfico normal de transacciones se generó sin ciclos. En datos reales existirían ciclos legítimos, que requerirían umbrales adicionales de monto y frecuencia.
- La enumeración de rutas alternativas es exponencial en el peor caso; se acota a 6 saltos y la red de canales es pequeña.
- Floyd-Warshall en Python puro es lento por encima de unos 300 nodos; por eso el modo completo de comparación llega solo a 300 nodos en todos los pares.
- Al restringirse a los algoritmos del curso, los puntos críticos se calculan en O(V·(V+E)) en lugar de O(V+E).

## 10. Control de versiones

Se recomienda usar commits descriptivos por módulo y marcar la versión entregada con una etiqueta:

```bash
git tag -a v1.0 -m "Entrega final Proyecto II"
git push origin v1.0
```
