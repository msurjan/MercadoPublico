"""
Cliente para la API de Licitaciones de Mercado Publico.

Base URL: https://api.mercadopublico.cl
Auth: el ticket va como parametro en la URL (query string), NO en un header.
Esto es distinto a Compra Agil - ver compra_agil_client.py.
"""
import requests
from datetime import datetime, timedelta

BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
MAX_DIAS_RANGO = 31  # tope de seguridad: no recorrer meses enteros en una sola busqueda


def obtener_licitaciones_activas(ticket: str) -> list:
    """
    Devuelve el listado de licitaciones actualmente en estado 'Publicada'
    (abiertas para recibir ofertas), sin importar su fecha de creacion.

    Segun documentacion oficial, estado=activas "muestra todas las
    licitaciones publicadas al dia de realizada la consulta" - es decir,
    todo lo que esta abierto AHORA, en una sola llamada.
    """
    params = {"estado": "activas", "ticket": ticket}
    respuesta = requests.get(BASE_URL, params=params, timeout=30)
    respuesta.raise_for_status()
    datos = respuesta.json()
    return datos.get("Listado") or []


def obtener_licitaciones_por_dia(ticket: str, fecha: datetime) -> list:
    """Trae las licitaciones PUBLICADAS ese dia especifico (formato API: ddmmaaaa)."""
    params = {"fecha": fecha.strftime("%d%m%Y"), "ticket": ticket}
    respuesta = requests.get(BASE_URL, params=params, timeout=30)
    respuesta.raise_for_status()
    datos = respuesta.json()
    return datos.get("Listado") or []


def obtener_licitaciones_por_rango(ticket: str, fecha_desde: datetime, fecha_hasta: datetime) -> list:
    """
    Recorre dia por dia el rango [fecha_desde, fecha_hasta] (ambos inclusive)
    y acumula todas las licitaciones publicadas en ese periodo. Sirve para
    poblar el historial progresivamente hacia atras en el tiempo, ya que
    estado=activas solo trae lo que esta abierto HOY.

    Tope de seguridad: MAX_DIAS_RANGO dias por llamada, para no convertir
    un click en el navegador en cientos de requests secuenciales.
    """
    dias_totales = (fecha_hasta - fecha_desde).days + 1
    if dias_totales > MAX_DIAS_RANGO:
        raise ValueError(
            f"El rango pedido ({dias_totales} dias) supera el tope de seguridad "
            f"de {MAX_DIAS_RANGO} dias. Pide un rango mas acotado."
        )

    vistos = {}
    fecha_actual = fecha_desde
    while fecha_actual <= fecha_hasta:
        items = obtener_licitaciones_por_dia(ticket, fecha_actual)
        for item in items:
            codigo = item.get("CodigoExterno")
            if codigo:
                vistos[codigo] = item
        fecha_actual += timedelta(days=1)

    return list(vistos.values())

