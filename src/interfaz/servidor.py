"""Servidor web local de la interfaz gráfica.

Solo usa la biblioteca estándar (http.server), así que funciona sin internet y
sin instalar nada adicional. Sirve la página de ``web/`` y una API JSON que
llama a los módulos del sistema.

    python main.py            -> abre la interfaz en el navegador
    python main.py --sin-navegador   -> solo inicia el servidor
"""

import json
import os
import threading
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from src.graph import ErrorValidacion
from src.interfaz import api
from src.utils import RAIZ, REPORTES_DIR

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
TIPOS = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".js": "application/javascript; charset=utf-8", ".png": "image/png",
         ".svg": "image/svg+xml", ".csv": "text/csv; charset=utf-8",
         ".txt": "text/plain; charset=utf-8", ".json": "application/json; charset=utf-8",
         ".pdf": "application/pdf"}


def _num(valor, defecto=None):
    try:
        return float(valor) if "." in str(valor) else int(valor)
    except (TypeError, ValueError):
        return defecto


RUTAS_GET = {
    "resumen": lambda q: api.resumen(),
    "red": lambda q: api.red_fisica(),
    "titularidad": lambda q: api.titularidad(),
    "fraude": lambda q: api.fraude(),
    "proximidad": lambda q: api.proximidad(q.get("cuenta", "E_ORO01"), _num(q.get("niveles"), 2)),
    "rastreo": lambda q: api.rastreo(q.get("cuenta", "LY_ORIG"), _num(q.get("minimo"), 0)),
    "cfc": lambda q: api.comparar_cfc(),
    "cuentas": lambda q: api.cuentas(),
    "enrutamiento": lambda q: api.red_enrutamiento(q.get("variante")),
    "tiempos": lambda q: api.matriz_tiempos(q.get("algoritmo", "floyd")),
    "troncal": lambda q: api.troncal(q.get("algoritmo", "kruskal"),
                                     json.loads(q.get("cerrados", "[]"))),
    "validacion": lambda q: api.validacion(),
    "huaico": lambda q: api.huaico(),
    "animacion": lambda q: api.animacion(q.get("algoritmo", "bfs"), q.get("red", "guia"),
                                         q.get("origen") or None),
    "reportes": lambda q: api.listar_reportes(),
}

RUTAS_POST = {
    "nodo": lambda d: api.editar_nodo(d["accion"], d["id"], d.get("atributos", {})),
    "arista": lambda d: api.editar_arista(d["accion"], d["u"], d["v"], d.get("atributos", {})),
    "restablecer": lambda d: api.restablecer(),
    "cargar": lambda d: api.cargar_archivo(d["nombre"], d["contenido"], d.get("dirigido", True)),
    "consulta": lambda d: api.consulta_ruta(d["origen"], d["destino"], float(d["monto"]),
                                            d.get("variante")),
    "liquidez": lambda d: api.liquidez(d.get("temporada", "alta"), d.get("metodo", "costo_minimo"),
                                       d.get("cerrados"), d.get("umbral_riesgo")),
    "comparacion": lambda d: api.comparacion(d.get("modo", "rapido")),
    "generar_reportes": lambda d: api.generar_reportes(),
}


class Manejador(BaseHTTPRequestHandler):
    def log_message(self, formato, *args):  # silencia el registro por petición
        pass

    def _responder(self, codigo, cuerpo, tipo="application/json; charset=utf-8"):
        datos = cuerpo if isinstance(cuerpo, bytes) else cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(datos)

    def _json(self, codigo, objeto):
        self._responder(codigo, json.dumps(api.limpiar(objeto), ensure_ascii=False))

    def _archivo(self, base, relativo):
        ruta = os.path.normpath(os.path.join(base, unquote(relativo)))
        if not ruta.startswith(os.path.normpath(base)) or not os.path.isfile(ruta):
            self._responder(404, "No encontrado", "text/plain; charset=utf-8")
            return
        with open(ruta, "rb") as f:
            contenido = f.read()
        tipo = TIPOS.get(os.path.splitext(ruta)[1].lower(), "application/octet-stream")
        self._responder(200, contenido, tipo)

    def _ejecutar(self, funcion, argumento):
        try:
            self._json(200, funcion(argumento))
        except (ErrorValidacion, ValueError, KeyError) as e:
            self._json(400, {"error": str(e).strip("'\"")})
        except Exception as e:  # error inesperado: se informa sin detener el servidor
            traceback.print_exc()
            self._json(500, {"error": f"Error interno: {e}"})

    def do_GET(self):
        url = urlparse(self.path)
        ruta = url.path
        if ruta in ("/", "/index.html"):
            return self._archivo(WEB_DIR, "index.html")
        if ruta.startswith("/static/"):
            return self._archivo(WEB_DIR, ruta[len("/static/"):])
        if ruta.startswith("/reportes/"):
            return self._archivo(REPORTES_DIR, ruta[len("/reportes/"):])
        if ruta.startswith("/docs/"):
            return self._archivo(os.path.join(RAIZ, "docs"), ruta[len("/docs/"):])
        if ruta.startswith("/api/"):
            nombre = ruta[len("/api/"):]
            if nombre in RUTAS_GET:
                consulta = {k: v[0] for k, v in parse_qs(url.query).items()}
                return self._ejecutar(RUTAS_GET[nombre], consulta)
        self._responder(404, "No encontrado", "text/plain; charset=utf-8")

    def do_POST(self):
        nombre = urlparse(self.path).path[len("/api/"):]
        if nombre not in RUTAS_POST:
            return self._responder(404, "No encontrado", "text/plain; charset=utf-8")
        largo = int(self.headers.get("Content-Length", 0))
        try:
            datos = json.loads(self.rfile.read(largo) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "JSON inválido"})
        self._ejecutar(RUTAS_POST[nombre], datos)


class Servidor(ThreadingHTTPServer):
    # En Windows, SO_REUSEADDR permite que dos programas usen el mismo puerto;
    # se desactiva para que, si 8050 está ocupado, se pruebe el siguiente.
    allow_reuse_address = os.name != "nt"
    daemon_threads = True


def iniciar(puerto=8050, abrir_navegador=True):
    servidor = None
    for p in range(puerto, puerto + 20):
        try:
            servidor = Servidor(("127.0.0.1", p), Manejador)
            break
        except OSError:
            continue
    if servidor is None:
        raise RuntimeError("No hay puertos libres entre 8050 y 8069.")
    url = f"http://127.0.0.1:{servidor.server_address[1]}/"
    print("=" * 64)
    print(" Sistema de Análisis y Optimización de Redes Financieras")
    print(" Caja Municipal Andina – interfaz gráfica")
    print(f" Abra en su navegador: {url}")
    print(" Presione Ctrl+C para detener el servidor.")
    print("=" * 64)
    if abrir_navegador:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()
