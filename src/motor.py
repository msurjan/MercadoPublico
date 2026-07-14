"""
Orquesta una corrida de busqueda completa: Licitaciones + Compra Agil,
filtradas por keyword, registrando todo en el almacen local (historial).

Esta funcion es el nucleo reutilizable: la llama ejecutar.bat (via
main.py) Y el boton "Buscar ahora" del navegador (via servidor.py), asi
que la logica vive en un solo lugar.
"""
from datetime import datetime, timezone

from clientes import licitaciones_client, compra_agil_client
from filtrado import filtrar_licitaciones
import almacen


def _filtrar_compra_agil_por_keywords(ticket: str, keywords: list, dias_hacia_atras: int, region, log) -> list:
    vistos = {}
    for kw in keywords:
        try:
            items = compra_agil_client.buscar_por_keyword(ticket, kw, dias_hacia_atras, region)
            for item in items:
                vistos[item.get("codigo")] = item
        except RuntimeError as e:
            log(f"  AVISO: {e}")
            break
        except Exception as e:
            log(f"  AVISO: fallo la busqueda de '{kw}' ({e}). Se omite y se sigue con las demas.")
            continue
    return list(vistos.values())


def ejecutar_busqueda(config: dict, keywords: list, ruta_estado_licitaciones: str,
                       ruta_estado_compra_agil: str, fecha_desde=None, fecha_hasta=None,
                       log=print) -> dict:
    """
    Ejecuta una corrida completa de busqueda y registra los resultados en
    el almacen local. Retorna un dict con las listas resultantes, listas
    para pasarle al generador de reporte.

    fecha_desde / fecha_hasta (datetime, opcionales): si se entregan, ADEMAS
    de consultar licitaciones activas, se recorre ese rango historico dia
    por dia para ir poblando el historial hacia atras en el tiempo.
    """
    ticket = config["ticket"]
    config_ca = config.get("compra_agil") or {}
    region = config_ca.get("region")
    dias_ca = config_ca.get("dias_hacia_atras", 3)

    log(f"Keywords: {', '.join(keywords)}")

    log("\n[1/4] Consultando Licitaciones activas...")
    try:
        licitaciones = licitaciones_client.obtener_licitaciones_activas(ticket)
        log(f"  -> {len(licitaciones)} licitaciones activas en total.")
    except Exception as e:
        log(f"  ERROR al consultar Licitaciones activas: {e}")
        licitaciones = []

    if fecha_desde and fecha_hasta:
        log(f"  Ademas, recorriendo rango historico {fecha_desde.date()} -> {fecha_hasta.date()}...")
        try:
            historicas = licitaciones_client.obtener_licitaciones_por_rango(ticket, fecha_desde, fecha_hasta)
            log(f"  -> {len(historicas)} licitaciones encontradas en ese rango.")
            vistos = {l.get("CodigoExterno"): l for l in licitaciones}
            for l in historicas:
                vistos[l.get("CodigoExterno")] = l
            licitaciones = list(vistos.values())
        except ValueError as e:
            log(f"  AVISO: {e}")
        except Exception as e:
            log(f"  ERROR al consultar rango historico: {e}")

    log("[2/4] Filtrando Licitaciones por tus keywords...")
    licitaciones_filtradas = filtrar_licitaciones(licitaciones, keywords)
    log(f"  -> {len(licitaciones_filtradas)} coinciden con tus habilidades.")
    almacen.registrar_encontrados(ruta_estado_licitaciones, licitaciones, "CodigoExterno")

    log("[3/4] Consultando Compra Agil (por keyword + completa)...")
    ca_filtrada = _filtrar_compra_agil_por_keywords(ticket, keywords, dias_ca, region, log)
    log(f"  -> {len(ca_filtrada)} coinciden con tus habilidades.")

    try:
        ca_todas = compra_agil_client.obtener_todas_recientes(ticket, dias_ca, region)
        log(f"  -> {len(ca_todas)} Compra Agil totales en los ultimos {dias_ca} dias.")
    except Exception as e:
        log(f"  ERROR al consultar Compra Agil (completa): {e}")
        ca_todas = []

    todas_ca_combinadas = {c.get("codigo"): c for c in ca_todas}
    for c in ca_filtrada:
        todas_ca_combinadas[c.get("codigo")] = c
    almacen.registrar_encontrados(ruta_estado_compra_agil, list(todas_ca_combinadas.values()), "codigo")

    log("[4/4] Busqueda completa.")

    return {
        "licitaciones_filtradas": licitaciones_filtradas,
        "ca_filtrada": ca_filtrada,
        "ca_todas": ca_todas,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
