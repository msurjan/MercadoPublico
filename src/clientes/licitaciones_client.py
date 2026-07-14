"""
Cliente para la API de Licitaciones de Mercado Publico.

Base URL: https://api.mercadopublico.cl
Auth: el ticket va como parametro en la URL (query string), NO en un header.
Esto es distinto a Compra Agil - ver compra_agil_client.py.
"""
import requests

BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"


def obtener_licitaciones_activas(ticket: str) -> list:
    """
    Devuelve el listado de licitaciones actualmente en estado 'Publicada'
    (abiertas para recibir ofertas), sin importar su fecha de creacion.

    Segun documentacion oficial, estado=activas "muestra todas las
    licitaciones publicadas al dia de realizada la consulta" - es decir,
    todo lo que esta abierto AHORA, en una sola llamada.

    LIMITACION CONOCIDA: si esta llamada devuelve un volumen muy grande
    de licitaciones (miles), puede ser necesario paginar o acotar por
    fecha en una version futura. Para el MVP se asume que el volumen de
    licitaciones activas en Chile es manejable en una sola respuesta.

    Retorna una lista de diccionarios (uno por licitacion). Lista vacia
    si no hay resultados.
    """
    params = {"estado": "activas", "ticket": ticket}
    respuesta = requests.get(BASE_URL, params=params, timeout=30)
    respuesta.raise_for_status()
    datos = respuesta.json()

    listado = datos.get("Listado") or []
    return listado
