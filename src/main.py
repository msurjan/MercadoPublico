"""
Punto de entrada para ejecutar.bat. Carga config/keywords, corre la
busqueda via motor.py, genera el reporte y levanta el servidor local.

Toda la logica de busqueda vive en motor.py para que el boton
"Buscar ahora" del navegador (via servidor.py) pueda invocar exactamente
lo mismo sin duplicar codigo.
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import motor
import servidor

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_CONFIG = os.path.join(RAIZ, "config", "config.local.json")
RUTA_KEYWORDS = os.path.join(RAIZ, "keywords.txt")
RUTA_ESTADO_LICITACIONES = os.path.join(RAIZ, "data", "historial_licitaciones.json")
RUTA_ESTADO_COMPRA_AGIL = os.path.join(RAIZ, "data", "historial_compra_agil.json")
RUTA_FAVORITOS = os.path.join(RAIZ, "data", "favoritos.json")
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


def main():
    print("=" * 50)
    print("BUSCADOR MERCADO PUBLICO")
    print("=" * 50)

    config = cargar_config()
    keywords = cargar_keywords()

    resultado = motor.ejecutar_busqueda(
        config, keywords, RUTA_ESTADO_LICITACIONES, RUTA_ESTADO_COMPRA_AGIL
    )

    print("\nGenerando reporte HTML...")
    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    favoritos_existentes = servidor.cargar_favoritos_existentes(RUTA_FAVORITOS)

    from reporte.generar_html import generar_reporte
    generar_reporte(
        resultado["licitaciones_filtradas"], resultado["ca_filtrada"], resultado["ca_todas"],
        keywords, RUTA_SALIDA, favoritos_existentes
    )
    print(f"  -> Reporte generado en: {RUTA_SALIDA}")

    servidor.iniciar_servidor(RUTA_SALIDA, RUTA_FAVORITOS, puerto=8765)


if __name__ == "__main__":
    main()
