"""
Servidor HTTP local minimo. Su unico proposito es permitir que el
reporte HTML guarde favoritos en disco con un clic, sin salir de tu
maquina y sin depender de servicios externos.

Se ejecuta SOLO mientras la ventana del programa esta abierta. Cerrarla
no borra los favoritos ya guardados - solo impide marcar nuevos hasta
la proxima corrida.
"""
import json
import os
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

_ruta_reporte = None
_ruta_favoritos = None


def _cargar_favoritos() -> dict:
    if not os.path.exists(_ruta_favoritos):
        return {}
    try:
        with open(_ruta_favoritos, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _guardar_favoritos(favoritos: dict):
    os.makedirs(os.path.dirname(_ruta_favoritos), exist_ok=True)
    with open(_ruta_favoritos, "w", encoding="utf-8") as f:
        json.dump(favoritos, f, ensure_ascii=False, indent=2)


def cargar_favoritos_existentes(ruta_favoritos: str) -> dict:
    """Se llama ANTES de generar el reporte, para saber que marcar como favorito ya."""
    global _ruta_favoritos
    _ruta_favoritos = ruta_favoritos
    return _cargar_favoritos()


class _ManejadorReporte(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silenciar logs HTTP en consola, no aportan nada al usuario

    def do_GET(self):
        if self.path in ("/", ""):
            with open(_ruta_reporte, "r", encoding="utf-8") as f:
                contenido = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(contenido.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/favorito":
            largo = int(self.headers.get("Content-Length", 0))
            datos = json.loads(self.rfile.read(largo))
            codigo = datos.get("codigo")
            favorito = datos.get("favorito")

            favoritos = _cargar_favoritos()
            if favorito:
                favoritos[codigo] = True
            else:
                favoritos.pop(codigo, None)
            _guardar_favoritos(favoritos)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        else:
            self.send_response(404)
            self.end_headers()


def _abrir_navegador_diferido(url: str):
    time.sleep(1)
    webbrowser.open(url)


def iniciar_servidor(ruta_reporte: str, ruta_favoritos: str, puerto: int = 8765):
    """Bloquea hasta que el usuario cierre la ventana (Ctrl+C o cerrar consola)."""
    global _ruta_reporte, _ruta_favoritos
    _ruta_reporte = ruta_reporte
    _ruta_favoritos = ruta_favoritos

    url = f"http://localhost:{puerto}/"
    threading.Thread(target=_abrir_navegador_diferido, args=(url,), daemon=True).start()

    servidor = HTTPServer(("localhost", puerto), _ManejadorReporte)
    print(f"\nReporte disponible en {url}")
    print("Deja esta ventana abierta mientras marcas favoritos.")
    print("Cuando termines de revisar, cierra esta ventana o presiona Ctrl+C.\n")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido. Tus favoritos quedaron guardados.")
