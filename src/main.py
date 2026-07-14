"""
Punto de entrada. Orquesta: leer config, leer keywords, llamar a ambas
APIs, filtrar por habilidad, generar el reporte HTML y abrirlo en el
navegador. Se ejecuta con doble clic via ejecutar.bat.
"""
import json
import os
import sys
import webbrowser
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clientes import licitaciones_client, compra_agil_client
from filtrado import filtrar_licitaciones

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_CONFIG = os.path.join(RAIZ, "config", "config.local.json")
RUTA_KEYWORDS = os.path.join(RAIZ, "keywords.txt")
RUTA_SALIDA = os.path.join(RAIZ, "output", f"reporte_{datetime.now().strftime('%Y%m%d_%H%M')}.html")


def cargar_config() -> dict:
    if not os.path.exists(RUTA_CONFIG):
        print("ERROR: no existe config/config.local.json")
        print("Copia config/config.example.json a config/config.local.json y pon tu ticket real.")
        sys.exit(1)
    with open(RUTA_CONFIG, "r", encoding="utf-8") as f:
        config = json.load(f)
    if not config.get("ticket") or config["ticket"] == "PEGA_TU_TICKET_AQUI":
        print("ERROR: falta configurar el ticket real en config/config.local.json")
        sys.exit(1)
    return config


def cargar_keywords() -> list:
    if not os.path.exists(RUTA_KEYWORDS):
        print("ERROR: no existe keywords.txt")
        sys.exit(1)
    with open(RUTA_KEYWORDS, "r", encoding="utf-8") as f:
        return [linea.strip() for linea in f if linea.strip()]


def filtrar_compra_agil_por_keywords(ticket: str, keywords: list, dias_hacia_atras: int, region) -> list:
    """La API acepta una sola keyword por llamada (q=). Se consulta una vez
    por keyword y se deduplica por codigo. Un error en UNA keyword no debe
    descartar lo ya encontrado en las demas."""
    vistos = {}
    for kw in keywords:
        try:
            items = compra_agil_client.buscar_por_keyword(ticket, kw, dias_hacia_atras, region)
            for item in items:
                vistos[item.get("codigo")] = item
        except RuntimeError as e:
            print(f"  AVISO: {e}")
            break  # cuota agotada: no tiene sentido seguir intentando otras keywords
        except Exception as e:
            print(f"  AVISO: fallo la busqueda de '{kw}' ({e}). Se omite y se sigue con las demas.")
            continue
    return list(vistos.values())


def main():
    print("=" * 50)
    print("BUSCADOR MERCADO PUBLICO")
    print("=" * 50)

    config = cargar_config()
    keywords = cargar_keywords()
    ticket = config["ticket"]
    config_ca = config.get("compra_agil") or {}
    region = config_ca.get("region")
    dias_ca = config_ca.get("dias_hacia_atras", 3)

    print(f"Keywords: {', '.join(keywords)}")

    print("\n[1/4] Consultando Licitaciones activas...")
    try:
        licitaciones = licitaciones_client.obtener_licitaciones_activas(ticket)
        print(f"  -> {len(licitaciones)} licitaciones activas en total.")
    except Exception as e:
        print(f"  ERROR al consultar Licitaciones: {e}")
        licitaciones = []

    print("[2/4] Filtrando Licitaciones por tus keywords...")
    licitaciones_filtradas = filtrar_licitaciones(licitaciones, keywords)
    print(f"  -> {len(licitaciones_filtradas)} coinciden con tus habilidades.")

    print("[3/4] Consultando Compra Agil (por keyword + completa)...")
    try:
        ca_filtrada = filtrar_compra_agil_por_keywords(ticket, keywords, dias_ca, region)
        print(f"  -> {len(ca_filtrada)} coinciden con tus habilidades.")
    except Exception as e:
        print(f"  ERROR al consultar Compra Agil (por keyword): {e}")
        ca_filtrada = []

    try:
        ca_todas = compra_agil_client.obtener_todas_recientes(ticket, dias_ca, region)
        print(f"  -> {len(ca_todas)} Compra Agil totales en los ultimos {dias_ca} dias.")
    except Exception as e:
        print(f"  ERROR al consultar Compra Agil (completa): {e}")
        ca_todas = []

    print("[4/4] Generando reporte HTML...")
    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)

    from reporte.generar_html import generar_reporte
    generar_reporte(licitaciones_filtradas, ca_filtrada, ca_todas, keywords, RUTA_SALIDA)
    print(f"  -> Reporte generado en: {RUTA_SALIDA}")

    webbrowser.open(f"file://{RUTA_SALIDA}")
    print("\nListo. El reporte se abrio en tu navegador.")


if __name__ == "__main__":
    main()
