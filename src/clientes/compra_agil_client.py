"""
Cliente para la API v2 de Compra Agil de Mercado Publico.

Base URL: https://api2.mercadopublico.cl
Auth: el ticket va en un HEADER HTTP ("ticket: TU_TICKET"), NO en la URL.
Esto es distinto a Licitaciones - ver licitaciones_client.py.
"""
import requests
import time
from datetime import datetime, timezone, timedelta

BASE_URL = "https://api2.mercadopublico.cl/v2/compra-agil"
TAMANO_PAGINA = 50
MAX_PAGINAS_SEGURIDAD = 20  # tope duro: 20 x 50 = 1000 resultados por keyword como maximo

# Estados relevantes para alguien buscando oportunidades activas u
# observando resultados recientes. Se excluye 'cancelada' y 'desierta'
# por defecto porque no representan una oportunidad de negocio.
ESTADOS_RELEVANTES = "publicada,proveedor_seleccionado,cerrada"


def _headers(ticket: str) -> dict:
    return {"ticket": ticket}


def _rango_fechas(dias_hacia_atras: int) -> dict:
    ahora = datetime.now(timezone.utc)
    desde = ahora - timedelta(days=dias_hacia_atras)
    return {
        "publicado_desde": desde.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publicado_hasta": ahora.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _paginar(ticket: str, params: dict, etiqueta: str = "") -> list:
    """
    Recorre todas las paginas de un listado y devuelve los items acumulados.
    Imprime progreso pagina por pagina para que nunca parezca "pegado".
    """
    items = []
    params = dict(params)
    params.setdefault("tamano_pagina", TAMANO_PAGINA)
    params.setdefault("numero_pagina", 1)

    while True:
        resp = requests.get(BASE_URL, headers=_headers(ticket), params=params, timeout=30)
        if resp.status_code == 429:
            raise RuntimeError(
                "Cuota diaria de la API de Compra Agil agotada. "
                "Reintenta despues de medianoche (hora del servidor)."
            )
        if resp.status_code == 500:
            print(f"    ... {etiqueta}: error 500 del servidor, reintentando en 3s...")
            time.sleep(3)
            resp = requests.get(BASE_URL, headers=_headers(ticket), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        payload = data.get("payload") or {}
        items.extend(payload.get("items", []))

        paginacion = payload.get("paginacion", {})
        pagina_actual = paginacion.get("numero_pagina", 1)
        total_paginas = paginacion.get("total_paginas", 1)
        total_resultados = paginacion.get("total_resultados", len(items))

        print(f"    ... {etiqueta} pagina {pagina_actual}/{total_paginas} "
              f"({len(items)}/{total_resultados} resultados acumulados)")

        if pagina_actual >= total_paginas:
            break
        if pagina_actual >= MAX_PAGINAS_SEGURIDAD:
            print(f"    AVISO: '{etiqueta}' supera el limite de seguridad de "
                  f"{MAX_PAGINAS_SEGURIDAD} paginas. Se corta aqui - probablemente "
                  f"la keyword es demasiado generica (revisa si tiene caracteres "
                  f"especiales como '+' o '&').")
            break
        params["numero_pagina"] = pagina_actual + 1

    return items


def buscar_por_keyword(ticket: str, keyword: str, dias_hacia_atras: int, region=None) -> list:
    """
    Busca Compras Agiles que contengan la keyword dada en nombre/descripcion,
    usando el parametro nativo q= de la API, ACOTADO a los ultimos N dias
    (sin esto, la busqueda recorre anios de historial y puede tardar minutos
    para keywords genericas).
    """
    params = {"q": keyword, "estado": ESTADOS_RELEVANTES}
    params.update(_rango_fechas(dias_hacia_atras))
    if region:
        params["region"] = region
    return _paginar(ticket, params, etiqueta=f"keyword='{keyword}'")


def obtener_todas_recientes(ticket: str, dias_hacia_atras: int, region=None) -> list:
    """
    Trae TODAS las Compras Agiles publicadas en los ultimos N dias, sin
    filtrar por keyword. Alimenta la tabla de navegacion libre del reporte
    (para detectar oportunidades de compra/venta simple fuera de tu expertise).
    """
    params = _rango_fechas(dias_hacia_atras)
    if region:
        params["region"] = region
    return _paginar(ticket, params, etiqueta="listado completo")
