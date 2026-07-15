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
# Tope de seguridad real (protege contra bugs/loops infinitos), no un limite
# practico - con el progreso visible en el navegador ya no hace falta cortar
# temprano solo para que la espera no parezca "colgada".
MAX_PAGINAS_SEGURIDAD = 300  # 300 x 50 = 15.000 resultados como maximo absoluto

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
        try:
            resp = requests.get(BASE_URL, headers=_headers(ticket), params=params, timeout=30)
            if resp.status_code == 429:
                raise RuntimeError(
                    "Cuota diaria de la API de Compra Agil agotada. "
                    "Reintenta despues de medianoche (hora del servidor)."
                )
            if resp.status_code in (500, 502, 503, 504):
                print(f"    ... {etiqueta}: error {resp.status_code} del servidor, reintentando en 3s...")
                time.sleep(3)
                resp = requests.get(BASE_URL, headers=_headers(ticket), params=params, timeout=30)
            resp.raise_for_status()
        except RuntimeError:
            raise
        except Exception as e:
            print(f"    AVISO: '{etiqueta}' fallo en pagina {params.get('numero_pagina')} ({e}). "
                  f"Se conservan los {len(items)} resultados ya descargados hasta aqui.")
            break

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


LIMITE_API_TOTAL_RESULTADOS = 9500  # margen de seguridad bajo el techo real de 10.000 de la API
PROFUNDIDAD_MAXIMA_DIVISION = 12    # protege contra recursion infinita si algo sale raro


def _consultar_total(ticket: str, params: dict) -> int:
    """Consulta 1 pagina (tamano minimo valido de la API) para conocer el total_resultados real."""
    params_prueba = dict(params, tamano_pagina=TAMANO_PAGINA, numero_pagina=1)
    resp = requests.get(BASE_URL, headers=_headers(ticket), params=params_prueba, timeout=30)
    resp.raise_for_status()
    payload = resp.json().get("payload") or {}
    return payload.get("paginacion", {}).get("total_resultados", 0)


def _obtener_rango_seguro(ticket: str, desde: datetime, hasta: datetime, region, log, profundidad: int = 0) -> list:
    """
    Trae todos los resultados del rango [desde, hasta]. Si el total roza
    el techo real de la API (10.000, mas alla del cual la paginacion deja
    de ser confiable), divide el rango en dos mitades y repite - para que
    nunca se pierdan resultados por el limite de la API, no del nuestro.
    """
    params = {
        "publicado_desde": desde.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publicado_hasta": hasta.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if region:
        params["region"] = region

    total = _consultar_total(ticket, params)
    rango_es_divisible = (hasta - desde).total_seconds() > 3600  # no dividir rangos de menos de 1 hora

    if total >= LIMITE_API_TOTAL_RESULTADOS and rango_es_divisible and profundidad < PROFUNDIDAD_MAXIMA_DIVISION:
        medio = desde + (hasta - desde) / 2
        log(f"    AVISO: rango {desde.date()} -> {hasta.date()} tiene {total}+ resultados "
            f"(cerca del techo real de la API). Dividiendo en dos mitades para no perder datos...")
        parte1 = _obtener_rango_seguro(ticket, desde, medio, region, log, profundidad + 1)
        parte2 = _obtener_rango_seguro(ticket, medio, hasta, region, log, profundidad + 1)
        vistos = {c.get("codigo"): c for c in parte1}
        for c in parte2:
            vistos[c.get("codigo")] = c
        return list(vistos.values())

    return _paginar(ticket, params, etiqueta=f"{desde.date()}->{hasta.date()}")


def obtener_todas_recientes(ticket: str, dias_hacia_atras: int, region=None, log=print) -> list:
    """
    Trae TODAS las Compras Agiles publicadas en los ultimos N dias, sin
    filtrar por keyword. Alimenta la tabla de navegacion libre del reporte
    (para detectar oportunidades de compra/venta simple fuera de tu expertise).

    Divide automaticamente el rango si se acerca al techo real de 10.000
    resultados de la API, para garantizar que no queden gaps de fechas.
    """
    ahora = datetime.now(timezone.utc)
    desde = ahora - timedelta(days=dias_hacia_atras)
    return _obtener_rango_seguro(ticket, desde, ahora, region, log)
