"""
Orquesta una corrida de busqueda completa: Licitaciones + Compra Agil,
registrando todo en el almacen local (historial).

Esta funcion es el nucleo reutilizable: la llama ejecutar.bat (via
main.py, solo para validar config) Y el boton "Buscar ahora" del
navegador (via servidor.py), asi que la logica vive en un solo lugar.

NOTA: Compra Agil ya NO se busca por keyword via la API (q=). Se trae
TODO lo disponible en el rango de fechas/region configurado, y el
filtrado por habilidad se hace en el navegador con los botones de
busqueda rapida (presets) - evita duplicar trabajo entre "por habilidad"
y "todo", que en la practica terminaban mostrando casi lo mismo.
"""
from datetime import datetime, timezone

from clientes import licitaciones_client, compra_agil_client
from filtrado import filtrar_licitaciones
import almacen


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

    log("\n[1/3] Consultando Licitaciones activas...")
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

    log("[2/3] Filtrando Licitaciones por tus keywords...")
    licitaciones_filtradas = filtrar_licitaciones(licitaciones, keywords)
    log(f"  -> {len(licitaciones_filtradas)} coinciden con tus habilidades.")
    almacen.registrar_encontrados(ruta_estado_licitaciones, licitaciones, "CodigoExterno")

    log("[3/3] Consultando Compra Agil...")
    try:
        ca_todas = compra_agil_client.obtener_todas_recientes(ticket, dias_ca, region, log=log)
        log(f"  -> {len(ca_todas)} Compra Agil totales en los ultimos {dias_ca} dias.")
    except Exception as e:
        log(f"  ERROR al consultar Compra Agil: {e}")
        ca_todas = []
    almacen.registrar_encontrados(ruta_estado_compra_agil, ca_todas, "codigo")

    log("Busqueda completa.")

    return {
        "licitaciones_filtradas": licitaciones_filtradas,
        "ca_todas": ca_todas,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
