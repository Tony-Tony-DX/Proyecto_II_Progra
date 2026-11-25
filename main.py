"""Sistema de Análisis y Optimización de Redes Financieras – Caja Municipal Andina.

Uso:
    python main.py                  interfaz gráfica (se abre en el navegador)
    python main.py --terminal       menú interactivo en la terminal
    python main.py --reportes       genera todos los reportes en reportes/ sin preguntar
    python main.py --datos          regenera los datos simulados (semilla 2026)
    python main.py --sin-navegador  inicia la interfaz sin abrir el navegador
"""

import sys

from src import analisis_transacciones as at
from src import distribucion_liquidez as dl
from src import enrutamiento_financiero as ef
from src import evaluacion_resultados as ev
from src import gestion_red as gr
from src.algoritmos.recorridos import kosaraju, tarjan
from src.generador_datos import guardar as generar_datos
from src.graph import ErrorValidacion
from src.utils import a_numero, formatear_tabla, guardar_texto, medir

HUAICO = [("OLL", "SMA")]


# ------------------------------------------------------------- entrada
def preguntar(texto, defecto=None):
    sufijo = f" [{defecto}]" if defecto is not None else ""
    try:
        valor = input(f"{texto}{sufijo}: ").strip()
    except EOFError:
        valor = ""
    return valor if valor else ("" if defecto is None else str(defecto))


def preguntar_numero(texto, defecto):
    valor = a_numero(preguntar(texto, defecto))
    if not isinstance(valor, (int, float)):
        print("  Valor no numérico; se usa el valor por defecto.")
        return defecto
    return valor


def atributos_desde_texto(texto):
    """'capacidad=500, riesgo=3' -> {'capacidad': 500, 'riesgo': 3}"""
    atributos = {}
    for parte in texto.split(","):
        if "=" in parte:
            k, v = parte.split("=", 1)
            atributos[k.strip()] = a_numero(v)
    return atributos


def mostrar_y_guardar(texto, archivo):
    print(texto)
    print(f"\n  Reporte guardado en {guardar_texto(archivo, texto)}")


def menu(titulo, opciones):
    while True:
        print("\n" + "=" * 72)
        print(titulo)
        print("=" * 72)
        for clave, (descripcion, _) in opciones.items():
            print(f"  {clave}. {descripcion}")
        print("  0. Volver")
        eleccion = preguntar("Opción", "0")
        if eleccion == "0":
            return
        if eleccion in opciones:
            try:
                opciones[eleccion][1]()
            except (ErrorValidacion, ValueError, KeyError) as e:
                print(f"\n  Error: {e}")


# ------------------------------------------------------- módulo 1
class Sesion:
    red_fisica = None

    @classmethod
    def fisica(cls):
        if cls.red_fisica is None:
            cls.red_fisica = gr.cargar_red_fisica()
        return cls.red_fisica


def m1_resumen():
    redes = [Sesion.fisica(), gr.cargar_red_liquidez(), gr.cargar_red_enrutamiento(),
             gr.cargar_titularidad()]
    texto = "\n\n".join(gr.resumen(r) for r in redes)
    problemas = gr.validar_titularidad(redes[3])
    texto += "\n\nTitularidad bipartita (clientes / cuentas): " + ("sí" if not problemas else "; ".join(problemas))
    mostrar_y_guardar(texto, "m1_resumen_redes.txt")


def m1_visualizar():
    ruta = gr.visualizar(Sesion.fisica(), "m1_red_fisica.png",
                         "Red física de la Caja Municipal Andina (esquema sobre coordenadas)")
    print(f"  Imagen guardada en {ruta}")


def m1_agregar_nodo():
    g = Sesion.fisica()
    nodo = preguntar("Identificador del nodo")
    tipo = preguntar("Tipo (agencia, cajero, agente, paso, boveda_regional...)", "agencia")
    extra = atributos_desde_texto(preguntar("Atributos extra (ej. lat=-13.5, lon=-71.9, demanda_alta=300)", ""))
    g.agregar_nodo(nodo, tipo=tipo, nombre=nodo, **extra)
    print(f"  Nodo {nodo} agregado. {g}")


def m1_modificar_nodo():
    g = Sesion.fisica()
    nodo = preguntar("Nodo a modificar")
    g.modificar_nodo(nodo, **atributos_desde_texto(preguntar("Atributos (ej. demanda_alta=500)")))
    print(f"  {nodo}: {g.nodos[nodo]}")


def m1_eliminar_nodo():
    g = Sesion.fisica()
    g.eliminar_nodo(preguntar("Nodo a eliminar"))
    print(f"  Nodo eliminado. {g}")


def m1_arista():
    g = Sesion.fisica()
    accion = preguntar("Acción: agregar / modificar / eliminar", "agregar")
    u, v = preguntar("Origen"), preguntar("Destino")
    if accion == "eliminar":
        g.eliminar_arista(u, v)
    elif accion == "modificar":
        g.modificar_arista(u, v, **atributos_desde_texto(preguntar("Atributos (ej. riesgo=9)")))
    else:
        g.agregar_arista(u, v, **atributos_desde_texto(
            preguntar("Atributos", "tipo_via=carretera, distancia_km=10, tiempo_h=0.5, riesgo=3")))
    print(f"  Listo. {g}")


def m1_cargar_externo():
    ruta = preguntar("Ruta del archivo (.csv de aristas, .txt o .json)")
    if ruta.endswith(".json"):
        g = gr.cargar_json(ruta)
    elif ruta.endswith(".txt"):
        g = gr.cargar_txt(ruta, preguntar("¿Dirigido? (s/n)", "s") == "s")
    else:
        from src.graph import Grafo
        g = Grafo(preguntar("¿Dirigido? (s/n)", "s") == "s", True, ruta)
        gr.cargar_aristas_csv(g, ruta, crear_nodos=True)
    print(gr.resumen(g))


def m1_guardar_json():
    ruta = gr.guardar_json(Sesion.fisica(), preguntar("Archivo de salida", "reportes/red_fisica.json"))
    print(f"  Red guardada en {ruta}")


def m1_restablecer():
    Sesion.red_fisica = gr.cargar_red_fisica()
    print("  Red física recargada desde data/.")


# ------------------------------------------------------- módulo 2
def _analisis():
    tit = gr.cargar_titularidad()
    cuentas = [n for n, a in tit.nodos.items() if a["tipo"] == "cuenta"]
    tiempos = ef.matriz_tiempos(gr.cargar_red_fisica())
    return at.analizar(at.cargar_transacciones(), at.cargar_retiros(), tiempos, cuentas)


def m2_completo():
    res = _analisis()
    mostrar_y_guardar(at.generar_reporte(res), "m2_reporte_transacciones.txt")
    print(f"  Alertas en CSV: {at.exportar_alertas(res)}")


def m2_rastrear():
    grafo = at.construir_grafo(at.cargar_transacciones())
    cuenta = preguntar("Cuenta de origen", "LY_ORIG")
    minimo = preguntar_numero("Monto mínimo por relación a seguir (S/)", 10000)
    caminos, intermedios, receptores = at.rastrear(grafo, cuenta, 6, minimo)
    L = [f"Rastreo de fondos desde {cuenta} (DFS, relaciones >= S/ {minimo:,})"]
    for c in caminos[:30]:
        L.append("  " + " -> ".join(c))
    L.append(f"Intermediarios: {', '.join(intermedios) or 'ninguno'}")
    L.append(f"Receptores finales: {', '.join(receptores) or 'ninguno'}")
    mostrar_y_guardar("\n".join(L), f"m2_rastreo_{cuenta}.txt")


def m2_proximidad():
    grafo = at.construir_grafo(at.cargar_transacciones())
    cuenta = preguntar("Cuenta marcada", "E_ORO01")
    niveles = at.proximidad(grafo, [cuenta], int(preguntar_numero("Niveles", 2)))
    for nivel, cuentas in niveles.items():
        print(f"  A {nivel} salto(s): {len(cuentas)} cuentas: {', '.join(cuentas[:25])}")


def m2_cfc():
    grafo = at.construir_grafo(at.cargar_transacciones())
    c1, t1, k1 = medir(kosaraju, grafo)
    c2, t2, k2 = medir(tarjan, grafo)
    grandes = [sorted(c) for c in c2 if len(c) > 1]
    print(formatear_tabla([["Kosaraju", len(c1), round(t1 * 1000, 2), round(k1, 1)],
                           ["Tarjan", len(c2), round(t2 * 1000, 2), round(k2, 1)]],
                          ["Algoritmo", "Componentes", "Tiempo ms", "Memoria KB"]))
    print(f"  Componentes con más de una cuenta: {grandes}")


# ------------------------------------------------------- módulo 3
def m3_escenarios():
    enr = gr.cargar_red_enrutamiento()
    texto = "\n\n".join(ef.reporte_operacion(enr, o, d, m, t) for t, o, d, m in ef.ESCENARIOS)
    mostrar_y_guardar(texto, "m3_reporte_enrutamiento.txt")


def m3_personalizada():
    enr = gr.cargar_red_enrutamiento(preguntar("Variante de red (vacío / promo / ruleteo)", "") or None)
    print("  Nodos: " + ", ".join(enr.nodos))
    o = preguntar("Origen", "CTA_CMA_QUI")
    d = preguntar("Destino", "CTA_BX_LIMA")
    m = preguntar_numero("Monto (S/)", 5000)
    print(ef.reporte_operacion(enr, o, d, m))


def m3_promo():
    texto = [ef.reporte_operacion(gr.cargar_red_enrutamiento("promo"), "CTA_CMA_QUI", "CTA_BX_LIMA", 400,
                                  "Campaña CyberDays: cashback de S/ 4 entre billeteras (monto S/ 400)")]
    rul = ef.detectar_ruleteo(gr.cargar_red_enrutamiento("ruleteo"), 400)
    texto.append("\nDetección de ruleteo con Bellman-Ford (red con devolución a cuenta CMA):")
    if rul:
        texto.append("  ALERTA: ciclo negativo " + " -> ".join(rul["ciclo"])
                     + f" (ganancia de S/ {-rul['costo_por_vuelta']:.2f} por vuelta)")
        texto.append("  Repetir el ciclo genera dinero sin límite: se reporta al módulo 2 como posible abuso.")
    else:
        texto.append("  Sin ciclos negativos.")
    mostrar_y_guardar("\n".join(texto), "m3_promociones_ruleteo.txt")


def m3_matriz():
    red = gr.cargar_red_fisica()
    puntos = red.nodos_por_tipo("boveda_central") + red.nodos_por_tipo("boveda_regional")
    puntos += ["MPP", "OCO", "QCM", "YAU"]
    algoritmo = preguntar("Algoritmo (floyd / johnson)", "floyd")
    tiempos = ef.matriz_tiempos(red, algoritmo)
    filas = [[u] + [round(tiempos[u][v], 2) for v in puntos] for u in puntos]
    mostrar_y_guardar("Tiempo mínimo de viaje en horas (" + algoritmo + ")\n"
                      + formatear_tabla(filas, ["Desde/hacia"] + puntos), "m3_matriz_tiempos.txt")


# ------------------------------------------------------- módulo 4
def _plan(temporada, cerrar=None, archivo="m4_plan.txt"):
    grafo = gr.cargar_red_liquidez(cerrar)
    metodo = preguntar("Método (costo_minimo / edmonds_karp / ford_fulkerson)", "costo_minimo")
    plan = dl.planificar(grafo, temporada, metodo)
    titulo = " (con huaico en Abra Málaga)" if cerrar else ""
    mostrar_y_guardar(dl.reporte_plan(plan) + titulo, archivo)
    print(f"  Flujos por ruta en CSV: {dl.exportar_plan(plan, archivo.replace('.txt', '.csv'))}")
    fisica = gr.cargar_red_fisica(cerrar)
    saturadas = [(r["origen"], r["destino"]) for r in plan["saturadas"]
                 if fisica.existe_arista(r["origen"], r["destino"])]
    pendientes = [d["nodo"] for d in plan["pendientes"]]
    ruta = gr.visualizar(fisica, archivo.replace(".txt", ".png"),
                         f"Distribución de liquidez – temporada {temporada}{titulo} "
                         "(rojo: rutas saturadas / puntos con demanda pendiente)",
                         resaltar_aristas=saturadas, resaltar_nodos=pendientes)
    print(f"  Mapa guardado en {ruta}")


def m4_normal():
    _plan("normal", None, "m4_plan_normal.txt")


def m4_alta():
    _plan("alta", None, "m4_plan_alta.txt")


def m4_huaico():
    _plan("alta", HUAICO, "m4_plan_alta_huaico.txt")


def m4_troncal():
    fisica = gr.cargar_red_fisica()
    algoritmo = preguntar("Algoritmo (kruskal / prim)", "kruskal")
    troncal = dl.red_troncal(fisica, "riesgo", algoritmo)
    mostrar_y_guardar(dl.reporte_red_troncal(troncal, dl.nodos_criticos(fisica)), "m4_red_troncal.txt")
    ruta = gr.visualizar(fisica, "m4_red_troncal.png", "Red troncal de menor riesgo (rojo)",
                         resaltar_aristas=[(u, v) for u, v, _ in troncal["aristas"]])
    print(f"  Mapa guardado en {ruta}")


# ------------------------------------------------------- módulo 5
def m5_validacion():
    mostrar_y_guardar(ev.reporte_validacion(ev.validar_escenarios()), "m5_validacion.txt")


def m5_comparacion():
    modo = preguntar("Modo (rapido / completo)", "rapido")
    print("  Ejecutando comparaciones... (el modo completo puede tardar varios minutos)")
    filas = ev.ejecutar_comparaciones(modo)
    mostrar_y_guardar(ev.reporte_comparaciones(filas), "m5_comparacion_algoritmos.txt")
    print(f"  CSV: {ev.exportar_comparaciones(filas)}")
    print(f"  Gráfica: {ev.graficar_comparaciones(filas)}")


def m5_huaico():
    mostrar_y_guardar(ev.reporte_huaico(ev.escenario_huaico()), "m5_escenario_huaico.txt")


# ------------------------------------------------------- todo
def generar_todo():
    import builtins
    original = builtins.input
    builtins.input = lambda *a, **k: ""  # acepta los valores por defecto
    try:
        for paso in (m1_resumen, m1_visualizar, m2_completo, m3_escenarios, m3_promo, m3_matriz,
                     m4_normal, m4_alta, m4_huaico, m4_troncal, m5_validacion, m5_comparacion,
                     m5_huaico):
            print(f"\n>>> {paso.__name__}")
            paso()
    finally:
        builtins.input = original


MENU_PRINCIPAL = {
    "1": ("Gestión y modelamiento de la red", lambda: menu("MÓDULO 1 · Gestión y modelamiento de la red", {
        "1": ("Resumen y validación de todas las redes", m1_resumen),
        "2": ("Visualizar la red física (PNG)", m1_visualizar),
        "3": ("Agregar nodo a la red física", m1_agregar_nodo),
        "4": ("Modificar nodo", m1_modificar_nodo),
        "5": ("Eliminar nodo", m1_eliminar_nodo),
        "6": ("Agregar, modificar o eliminar arista", m1_arista),
        "7": ("Cargar una red externa (CSV, TXT o JSON)", m1_cargar_externo),
        "8": ("Guardar la red física en JSON", m1_guardar_json),
        "9": ("Restablecer la red física desde data/", m1_restablecer),
    })),
    "2": ("Análisis de transacciones (fraude y lavado)", lambda: menu("MÓDULO 2 · Detección de operaciones sospechosas", {
        "1": ("Análisis completo y reporte", m2_completo),
        "2": ("Rastrear fondos desde una cuenta (DFS)", m2_rastrear),
        "3": ("Proximidad a una cuenta marcada (BFS)", m2_proximidad),
        "4": ("Comparar Kosaraju y Tarjan en la red real", m2_cfc),
    })),
    "3": ("Enrutamiento de operaciones y comisiones", lambda: menu("MÓDULO 3 · Enrutamiento y comisiones", {
        "1": ("Escenarios de Cusco (reporte comparativo)", m3_escenarios),
        "2": ("Consulta personalizada", m3_personalizada),
        "3": ("Campaña de cashback y detección de ruleteo", m3_promo),
        "4": ("Matriz de tiempos entre ciudades (Floyd-Warshall / Johnson)", m3_matriz),
    })),
    "4": ("Distribución de liquidez", lambda: menu("MÓDULO 4 · Distribución de liquidez", {
        "1": ("Plan para temporada normal", m4_normal),
        "2": ("Plan para temporada alta (Inti Raymi)", m4_alta),
        "3": ("Plan para temporada alta con huaico en Abra Málaga", m4_huaico),
        "4": ("Red troncal de menor riesgo y puntos críticos", m4_troncal),
    })),
    "5": ("Evaluación y validación", lambda: menu("MÓDULO 5 · Evaluación, comparación y validación", {
        "1": ("Validar escenarios con resultados esperados", m5_validacion),
        "2": ("Comparar algoritmos (tiempo y memoria)", m5_comparacion),
        "3": ("Escenario de contingencia: huaico", m5_huaico),
    })),
    "6": ("Generar todos los reportes", generar_todo),
}


def principal():
    # Evita que un carácter especial (tildes, flechas) detenga el programa en
    # consolas de Windows con codificación antigua.
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    if "--datos" in sys.argv:
        print("Datos generados: %d cuentas, %d transacciones, %d retiros." % generar_datos())
        return
    if "--reportes" in sys.argv:
        generar_todo()
        return
    if "--terminal" not in sys.argv:
        from src.interfaz.servidor import iniciar
        iniciar(abrir_navegador="--sin-navegador" not in sys.argv)
        return
    menu("SISTEMA DE ANÁLISIS Y OPTIMIZACIÓN DE REDES FINANCIERAS\n"
         "Caja Municipal Andina (entidad ficticia, datos simulados) – Cusco", MENU_PRINCIPAL)
    print("Hasta luego.")


if __name__ == "__main__":
    principal()
