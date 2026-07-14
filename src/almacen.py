"""
Almacen de estado local. Reemplaza a favoritos.json con un modelo mas
completo: por cada codigo (licitacion o compra agil) se guarda:

  {
    "codigo": {
      "estado": "nuevo" | "visto" | "favorito" | "descartado",
      "primera_vez_visto": "2026-07-14T20:00:00",
      "datos": { ...el diccionario completo devuelto por la API... }
    }
  }

"datos" se guarda para que el tab Historial pueda mostrar TODO lo
encontrado alguna vez, sin depender de que la API lo siga devolviendo
(una licitacion puede cerrar y dejar de aparecer en estado=activas,
pero igual queremos verla en el historial).

Nada se borra nunca desde esta capa. "descartado" es un estado, no
una eliminacion.
"""
import json
import os
from datetime import datetime

ESTADOS_VALIDOS = {"nuevo", "visto", "favorito", "descartado"}


def cargar_estado(ruta_estado: str) -> dict:
    if not os.path.exists(ruta_estado):
        return {}
    try:
        with open(ruta_estado, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def guardar_estado(ruta_estado: str, estado: dict):
    os.makedirs(os.path.dirname(ruta_estado), exist_ok=True)
    with open(ruta_estado, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


def registrar_encontrados(ruta_estado: str, items: list, campo_codigo: str) -> dict:
    """
    Fusiona una lista de items recien encontrados (licitaciones o compra
    agil) con el estado acumulado. Los codigos nuevos entran como
    'nuevo'; los que ya existian actualizan sus 'datos' pero CONSERVAN
    su estado (favorito/descartado/visto no se pisan con 'nuevo').

    Retorna el estado completo actualizado.
    """
    estado = cargar_estado(ruta_estado)
    ahora = datetime.now().isoformat()

    for item in items:
        codigo = item.get(campo_codigo)
        if not codigo:
            continue
        if codigo in estado:
            estado[codigo]["datos"] = item  # refrescar datos (ej: nuevo monto, nuevo estado de licitacion)
        else:
            estado[codigo] = {
                "estado": "nuevo",
                "primera_vez_visto": ahora,
                "datos": item,
            }

    guardar_estado(ruta_estado, estado)
    return estado


def cambiar_estado_item(ruta_estado: str, codigo: str, nuevo_estado: str) -> dict:
    if nuevo_estado not in ESTADOS_VALIDOS:
        raise ValueError(f"Estado invalido: {nuevo_estado}")
    estado = cargar_estado(ruta_estado)
    if codigo in estado:
        estado[codigo]["estado"] = nuevo_estado
        guardar_estado(ruta_estado, estado)
    return estado


def marcar_vistos(ruta_estado: str, codigos: list):
    """Pasa de 'nuevo' a 'visto' los codigos indicados (ej: al abrir el tab Historial)."""
    estado = cargar_estado(ruta_estado)
    cambiado = False
    for codigo in codigos:
        if codigo in estado and estado[codigo]["estado"] == "nuevo":
            estado[codigo]["estado"] = "visto"
            cambiado = True
    if cambiado:
        guardar_estado(ruta_estado, estado)
    return estado
