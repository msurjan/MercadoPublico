"""
Filtrado de texto por palabras clave. Insensible a mayusculas/minusculas
y a tildes, para que "geologia" encuentre "Geología" sin esfuerzo del
usuario.
"""
import unicodedata


def _normalizar(texto: str) -> str:
    if not texto:
        return ""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    return sin_tildes.lower()


def texto_coincide(texto: str, keywords: list) -> bool:
    """True si alguna keyword aparece dentro del texto normalizado."""
    texto_norm = _normalizar(texto)
    return any(_normalizar(kw) in texto_norm for kw in keywords if kw.strip())


def filtrar_licitaciones(licitaciones: list, keywords: list) -> list:
    """
    Filtra licitaciones cuyo Nombre (y Descripcion, si el listado la trae)
    contenga alguna de las keywords.

    LIMITACION MVP: el listado de 'activas' de la API solo garantiza
    informacion basica (Nombre). Si el campo Descripcion no viene incluido
    en esta respuesta, el filtro evalua solo el Nombre. Verificar en la
    primera corrida real que campos trae efectivamente el listado.
    """
    resultado = []
    for lic in licitaciones:
        nombre = lic.get("Nombre", "") or ""
        descripcion = lic.get("Descripcion", "") or ""
        if texto_coincide(f"{nombre} {descripcion}", keywords):
            resultado.append(lic)
    return resultado
