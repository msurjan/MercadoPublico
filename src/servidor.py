"""
Servidor HTTP local. Sirve el reporte y expone la API que usa el
navegador para:
  - Marcar/desmarcar favoritos (ya existia en v2.0 favoritos).
  - Ver y cambiar el estado de items en el Historial (visto/descartado).
  - Disparar una busqueda nueva desde el tab "Buscar" sin tocar la consola.

Se ejecuta SOLO mientras la ventana del programa esta abierta. Cerrarla
no borra nada de lo ya guardado en disco.
"""
import json
import os
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import almacen
import motor

# Configurado por iniciar_servidor() antes de arrancar
_rutas = {}
_progreso = {"activo": False, "mensaje": "", "inicio": None, "error": None}


def _cargar_frontera() -> dict:
    ruta = _rutas.get("frontera")
    if not ruta or not os.path.exists(ruta):
        return {}
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _guardar_frontera(frontera: dict):
    ruta = _rutas.get("frontera")
    if not ruta:
        return
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(frontera, f, ensure_ascii=False, indent=2)


def _calcular_rango_continuar() -> tuple:
    """
    Calcula el proximo rango de 31 dias hacia atras, continuando desde
    donde termino la ultima poblacion historica. Si nunca se ha corrido,
    empieza desde hoy hacia atras.
    """
    from datetime import timedelta
    frontera = _cargar_frontera()
    fecha_mas_antigua_str = frontera.get("licitaciones_hasta")

    if fecha_mas_antigua_str:
        fecha_hasta = datetime.fromisoformat(fecha_mas_antigua_str) - timedelta(days=1)
    else:
        fecha_hasta = datetime.now()
    fecha_desde = fecha_hasta - timedelta(days=30)
    return fecha_desde, fecha_hasta


def _favoritos_desde_almacen() -> dict:
    """Unica fuente de verdad para favoritos: el estado del almacen, no un archivo separado."""
    estado_lic = almacen.cargar_estado(_rutas["estado_licitaciones"])
    estado_ca = almacen.cargar_estado(_rutas["estado_compra_agil"])
    favoritos = {}
    for codigo, info in {**estado_lic, **estado_ca}.items():
        if info.get("estado") == "favorito":
            favoritos[codigo] = True
    return favoritos


def _regenerar_reporte():
    """Vuelve a leer el estado actual (sin re-buscar) y regenera el HTML servido."""
    from reporte.generar_html import generar_reporte

    estado_lic = almacen.cargar_estado(_rutas["estado_licitaciones"])
    estado_ca = almacen.cargar_estado(_rutas["estado_compra_agil"])
    favoritos = _favoritos_desde_almacen()

    licitaciones = [v["datos"] for v in estado_lic.values() if v["estado"] != "descartado"]
    compra_agil = [v["datos"] for v in estado_ca.values() if v["estado"] != "descartado"]

    generar_reporte(licitaciones, compra_agil, _rutas["keywords_actuales"], _rutas["reporte"], favoritos)


def _leer_keywords() -> list:
    if not os.path.exists(_rutas["keywords"]):
        return []
    with open(_rutas["keywords"], "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]


def _guardar_keywords(keywords: list):
    with open(_rutas["keywords"], "w", encoding="utf-8") as f:
        f.write("\n".join(keywords) + "\n")


def _cargar_config() -> dict:
    with open(_rutas["config"], "r", encoding="utf-8") as f:
        return json.load(f)


def _historial_combinado() -> list:
    """Une los dos historiales (licitaciones + compra agil) en una sola lista para el tab Historial."""
    resultado = []
    estado_lic = almacen.cargar_estado(_rutas["estado_licitaciones"])
    for codigo, info in estado_lic.items():
        datos = info.get("datos", {})
        comprador = datos.get("Comprador") or {}
        resultado.append({
            "codigo": codigo,
            "tabla": "licitaciones",
            "nombre": datos.get("Nombre", ""),
            "organismo": datos.get("NombreOrganismo", "") or comprador.get("NombreOrganismo", ""),
            "region": comprador.get("RegionUnidad", ""),
            "monto": datos.get("MontoEstimado"),
            "fecha_cierre": datos.get("FechaCierre", ""),
            "url": f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={codigo}",
            "estado_item": info.get("estado"),
            "primera_vez_visto": info.get("primera_vez_visto"),
        })
    estado_ca = almacen.cargar_estado(_rutas["estado_compra_agil"])
    for codigo, info in estado_ca.items():
        datos = info.get("datos", {})
        institucion = datos.get("institucion") or {}
        montos = datos.get("montos") or {}
        fechas = datos.get("fechas") or {}
        resultado.append({
            "codigo": codigo,
            "tabla": "compra_agil",
            "nombre": datos.get("nombre", ""),
            "organismo": institucion.get("organismo_comprador", ""),
            "region": institucion.get("nombre_region", ""),
            "monto": montos.get("monto_disponible_clp") or montos.get("monto_disponible"),
            "fecha_cierre": fechas.get("fecha_cierre", ""),
            "url": f"https://compra-agil.mercadopublico.cl/resumen-cotizacion/{codigo}",
            "estado_item": info.get("estado"),
            "primera_vez_visto": info.get("primera_vez_visto"),
        })
    resultado.sort(key=lambda x: x.get("primera_vez_visto") or "", reverse=True)
    return resultado


class _ManejadorReporte(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _json(self, status: int, payload: dict):
        cuerpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        if self.path in ("/", ""):
            with open(_rutas["reporte"], "r", encoding="utf-8") as f:
                contenido = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(contenido.encode("utf-8"))
        elif self.path == "/api/keywords":
            self._json(200, {"keywords": _leer_keywords()})
        elif self.path == "/api/historial":
            self._json(200, {"items": _historial_combinado()})
        elif self.path == "/api/progreso":
            segundos = int(time.time() - _progreso["inicio"]) if _progreso["inicio"] else 0
            self._json(200, {
                "activo": _progreso["activo"],
                "mensaje": _progreso["mensaje"],
                "error": _progreso["error"],
                "segundos": segundos,
            })
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        largo = int(self.headers.get("Content-Length", 0))
        cuerpo_crudo = self.rfile.read(largo) if largo else b"{}"
        try:
            datos = json.loads(cuerpo_crudo)
        except json.JSONDecodeError:
            self._json(400, {"ok": False, "error": "JSON invalido"})
            return

        if self.path == "/api/keywords":
            _guardar_keywords(datos.get("keywords", []))
            self._json(200, {"ok": True})

        elif self.path == "/api/estado":
            codigo = datos.get("codigo")
            tabla = datos.get("tabla")
            nuevo_estado = datos.get("estado")
            ruta = _rutas["estado_licitaciones"] if tabla == "licitaciones" else _rutas["estado_compra_agil"]
            try:
                almacen.cambiar_estado_item(ruta, codigo, nuevo_estado)
                _regenerar_reporte()  # mantener sincronizadas las estrellas en Resultados
                self._json(200, {"ok": True})
            except ValueError as e:
                self._json(400, {"ok": False, "error": str(e)})

        elif self.path == "/api/buscar":
            if _progreso["activo"]:
                self._json(409, {"ok": False, "error": "Ya hay una busqueda en curso."})
                return
            keywords = datos.get("keywords") or _leer_keywords()
            _guardar_keywords(keywords)
            _rutas["keywords_actuales"] = keywords

            if datos.get("continuar"):
                fecha_desde, fecha_hasta = _calcular_rango_continuar()
                fecha_desde_str = fecha_desde.isoformat()
                fecha_hasta_str = fecha_hasta.isoformat()
            else:
                fecha_desde_str = datos.get("fecha_desde")
                fecha_hasta_str = datos.get("fecha_hasta")

            hilo = threading.Thread(
                target=_ejecutar_busqueda_en_hilo,
                args=(keywords, fecha_desde_str, fecha_hasta_str),
                daemon=True,
            )
            hilo.start()
            self._json(200, {"ok": True, "iniciado": True, "fecha_desde": fecha_desde_str, "fecha_hasta": fecha_hasta_str})

        else:
            self.send_response(404)
            self.end_headers()


def _ejecutar_busqueda_en_hilo(keywords: list, fecha_desde_str, fecha_hasta_str):
    global _progreso
    _progreso = {"activo": True, "mensaje": "Iniciando...", "inicio": time.time(), "error": None}

    def log(texto: str):
        print(texto)
        texto_limpio = texto.strip()
        if texto_limpio:
            _progreso["mensaje"] = texto_limpio

    try:
        fecha_desde = datetime.fromisoformat(fecha_desde_str) if fecha_desde_str else None
        fecha_hasta = datetime.fromisoformat(fecha_hasta_str) if fecha_hasta_str else None
        config = _cargar_config()
        print("\n[Buscar ahora] Disparado desde el navegador...")
        motor.ejecutar_busqueda(
            config, keywords, _rutas["estado_licitaciones"], _rutas["estado_compra_agil"],
            fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, log=log,
        )
        if fecha_desde:
            _guardar_frontera({"licitaciones_hasta": fecha_desde.date().isoformat()})
        _regenerar_reporte()
        _progreso["mensaje"] = "Listo."
    except Exception as e:
        print(f"[Buscar ahora] ERROR: {e}")
        _progreso["error"] = str(e)
    finally:
        _progreso["activo"] = False


def _abrir_navegador_diferido(url: str):
    time.sleep(1)
    webbrowser.open(url)


class _ServidorResiliente(HTTPServer):
    allow_reuse_address = True  # evita quedar bloqueado en el puerto tras un cierre abrupto


def iniciar_servidor(rutas: dict, puerto: int = 8765):
    """
    rutas debe incluir: reporte, favoritos, keywords, config,
    estado_licitaciones, estado_compra_agil.

    El reporte inicial se genera a partir de lo que YA esta guardado en
    disco (historial de corridas anteriores) - no dispara una busqueda
    nueva. Buscar solo ocurre cuando el usuario aprieta "Buscar ahora"
    en el tab Buscar.

    Bloquea hasta que el usuario cierre la ventana (Ctrl+C o cerrar consola).
    """
    global _rutas
    _rutas = dict(rutas)
    _rutas["keywords_actuales"] = _leer_keywords()

    os.makedirs(os.path.dirname(_rutas["reporte"]), exist_ok=True)
    _regenerar_reporte()

    url = f"http://localhost:{puerto}/"

    try:
        servidor = _ServidorResiliente(("localhost", puerto), _ManejadorReporte)
    except OSError:
        print(f"\nERROR: el puerto {puerto} ya esta en uso.")
        print("Esto casi siempre significa que TIENES OTRA VENTANA de este programa")
        print("abierta en otro lado (otra consola negra, minimizada o en otro monitor).")
        print("Cierra TODAS las ventanas negras de Python que tengas abiertas y vuelve a intentar.")
        input("\nPresiona Enter para salir...")
        import sys
        sys.exit(1)

    threading.Thread(target=_abrir_navegador_diferido, args=(url,), daemon=True).start()

    print(f"\nReporte disponible en {url}")
    print("Deja esta ventana abierta mientras usas la aplicacion.")
    print("Cuando termines, cierra esta ventana o presiona Ctrl+C.\n")
    print("IMPORTANTE: si seleccionas texto en esta consola, Windows PAUSA todo")
    print("el programa hasta que sueltes. Desactivalo en Propiedades > Modo de")
    print("edicion rapida (clic derecho en la barra de titulo de esta ventana).\n")

    while True:
        try:
            servidor.serve_forever()
            break
        except KeyboardInterrupt:
            print("\nServidor detenido. Todo lo guardado quedo a salvo.")
            break
        except Exception as e:
            print(f"\nAVISO: error inesperado en el servidor ({e}). Reintentando...")
            continue
