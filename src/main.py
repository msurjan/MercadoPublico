"""
Punto de entrada para ejecutar.bat. Valida que la configuracion este
lista y levanta el servidor local con el reporte generado a partir del
historial ya guardado.

IMPORTANTE: este script YA NO dispara una busqueda automaticamente.
La busqueda ocurre cuando el usuario aprieta "Buscar ahora" en el tab
Buscar del navegador. Esto evita gastar cuota de la API y tiempo de
espera cada vez que simplemente quieres revisar lo que ya tenias.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import servidor

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_CONFIG = os.path.join(RAIZ, "config", "config.local.json")
RUTA_KEYWORDS = os.path.join(RAIZ, "keywords.txt")
RUTA_ESTADO_LICITACIONES = os.path.join(RAIZ, "data", "historial_licitaciones.json")
RUTA_ESTADO_COMPRA_AGIL = os.path.join(RAIZ, "data", "historial_compra_agil.json")
RUTA_FRONTERA = os.path.join(RAIZ, "data", "frontera_historica.json")
RUTA_SALIDA = os.path.join(RAIZ, "output", "reporte_actual.html")


def validar_config():
    if not os.path.exists(RUTA_CONFIG):
        print("ERROR: no existe config/config.local.json")
        print("Copia config/config.example.json a config/config.local.json y pon tu ticket real.")
        sys.exit(1)
    with open(RUTA_CONFIG, "r", encoding="utf-8") as f:
        config = json.load(f)
    if not config.get("ticket") or config["ticket"] == "PEGA_TU_TICKET_AQUI":
        print("ERROR: falta configurar el ticket real en config/config.local.json")
        sys.exit(1)
    if not os.path.exists(RUTA_KEYWORDS):
        print("ERROR: no existe keywords.txt")
        sys.exit(1)


def main():
    print("=" * 50)
    print("BUSCADOR MERCADO PUBLICO")
    print("=" * 50)

    validar_config()

    servidor.iniciar_servidor({
        "reporte": RUTA_SALIDA,
        "keywords": RUTA_KEYWORDS,
        "config": RUTA_CONFIG,
        "estado_licitaciones": RUTA_ESTADO_LICITACIONES,
        "estado_compra_agil": RUTA_ESTADO_COMPRA_AGIL,
        "frontera": RUTA_FRONTERA,
    }, puerto=8765)


if __name__ == "__main__":
    main()
