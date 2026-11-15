"""
=============================================================================
PROYECTO DE WEB SCRAPING — LINKEDIN JOBS
MÓDULO 2 (parte A): LIMPIEZA Y NORMALIZACIÓN DE OFERTAS
Responsable: Fanny
=============================================================================
Entrada : lista de diccionarios producida por scraper.extraer_ofertas()
          (o el archivo ofertas_extraidas.json que genera el Módulo 1).
Salida  : lista de diccionarios limpios, sin duplicados y con la ubicación
          separada en ciudad / región / país.

Flujo del módulo:
  Datos extraídos → LIMPIEZA → NORMALIZACIÓN → (filtros.py)

Diferencia entre los dos conceptos (para la exposición):
  - LIMPIAR     = corregir el dato sin cambiar lo que dice
                  ("  Asesor   Comercial " → "Asesor Comercial").
  - NORMALIZAR  = llevar el dato a una forma única para poder COMPARARLO
                  ("BOGOTÁ", "Bogotá", "bogota" → "bogota").
=============================================================================
"""

import json
import re
import unicodedata
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit

# Campos de texto que entrega el Módulo 1 (scraper.py)
CAMPOS_TEXTO = ("id", "titulo", "empresa", "ubicacion", "fecha_relativa")

# Campos que revisamos para informar datos incompletos
CAMPOS_REVISADOS = ("id", "titulo", "empresa", "ubicacion", "fecha_publicacion", "url")


# =============================================================================
# 1. LIMPIEZA
# =============================================================================
def limpiar_texto(valor: Any) -> Optional[str]:
    """
    Limpia un texto SIN cambiar su significado:
      - Si no es texto o queda vacío, devuelve None (dato faltante).
      - Unifica la forma Unicode (NFC) para que "á" sea siempre el mismo carácter.
      - Convierte espacios raros (tabulaciones, saltos de línea, espacio duro
        '\\xa0' del HTML) en espacios normales.
      - Quita espacios repetidos y los de los extremos.

    Ejemplo: "  Asesor comercial –  Cierre de Ventas\\n" → "Asesor comercial – Cierre de Ventas"
    """
    if not isinstance(valor, str):
        return None
    texto = unicodedata.normalize("NFC", valor)
    texto = re.sub(r"\s+", " ", texto).strip()  # \s incluye \xa0, \t y \n
    return texto if texto else None


def limpiar_url(url: Any) -> Optional[str]:
    """
    Deja solo la parte útil de la URL de la oferta.

    LinkedIn agrega parámetros de seguimiento (?position=1&refId=...&trackingId=...)
    que cambian en cada búsqueda y no identifican la oferta. Se eliminan.
    Si el valor no es una URL http/https válida, devuelve None.
    """
    texto = limpiar_texto(url)
    if not texto:
        return None
    partes = urlsplit(texto)
    if partes.scheme not in ("http", "https") or not partes.netloc:
        return None
    return urlunsplit((partes.scheme, partes.netloc, partes.path, "", ""))


def limpiar_fecha(fecha: Any) -> Optional[str]:
    """
    Acepta únicamente fechas con formato ISO AAAA-MM-DD (el atributo 'datetime'
    de la etiqueta <time>). Cualquier otro valor se trata como dato faltante.
    """
    texto = limpiar_texto(fecha)
    if texto and re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto):
        return texto
    return None


# =============================================================================
# 2. NORMALIZACIÓN
# =============================================================================
def normalizar_texto(valor: Any) -> str:
    """
    Convierte un texto a su "forma de comparación". Se usa SOLO para buscar y
    comparar; el texto original se conserva para mostrarlo.

    Pasos:
      1. Limpieza básica (limpiar_texto).
      2. Minúsculas con casefold()            "INGENIERO" → "ingeniero"
      3. Quitar tildes y diacríticos           "Bogotá"    → "bogota"
         (se descompone cada letra con NFD y se descartan las marcas 'Mn').
      4. Signos de puntuación → espacio        "D.C." → "d c", "Desarrollador/a" → "desarrollador a"
      5. Un solo espacio entre palabras.

    Nota: al quitar diacríticos la "ñ" queda como "n". Como la palabra buscada
    pasa por la misma función, la comparación sigue siendo coherente.
    Devuelve "" si el dato está vacío o no es texto.
    """
    texto = limpiar_texto(valor)
    if not texto:
        return ""
    texto = texto.casefold()
    descompuesto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return texto.strip()


def separar_ubicacion(ubicacion: Any) -> Dict[str, Optional[str]]:
    """
    Separa la ubicación en ciudad, región y país según las comas.

    Formatos reales encontrados en search.html:
      "Bogotá, Distrito Capital, Colombia"   → ciudad / región / país
      "Cundinamarca, Colombia"               → región / país  (sin ciudad)
      "Área metropolitana de Bogotá D.C."    → solo ciudad (área)
    """
    vacio = {"ciudad": None, "region": None, "pais": None}
    texto = limpiar_texto(ubicacion)
    if not texto:
        return vacio

    partes = [p.strip() for p in texto.split(",") if p.strip()]
    if len(partes) >= 3:
        return {"ciudad": partes[0], "region": partes[1], "pais": partes[-1]}
    if len(partes) == 2:
        return {"ciudad": None, "region": partes[0], "pais": partes[1]}
    if len(partes) == 1:
        return {"ciudad": partes[0], "region": None, "pais": None}
    return vacio


# =============================================================================
# 3. PROCESAMIENTO DE UNA OFERTA Y DE LA LISTA COMPLETA
# =============================================================================
def limpiar_oferta(oferta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aplica la limpieza a todos los campos de UNA oferta y agrega
    ciudad / región / país. No modifica el diccionario original.
    Los campos que falten quedan en None (nunca se inventan valores).
    """
    limpia: Dict[str, Any] = {campo: limpiar_texto(oferta.get(campo)) for campo in CAMPOS_TEXTO}
    limpia["fecha_publicacion"] = limpiar_fecha(oferta.get("fecha_publicacion"))
    limpia["url"] = limpiar_url(oferta.get("url"))
    limpia.update(separar_ubicacion(limpia["ubicacion"]))
    return limpia


def _clave_duplicado(oferta: Dict[str, Any]) -> str:
    """Clave para detectar ofertas repetidas: el id; si no hay id, título+empresa+ubicación."""
    if oferta.get("id"):
        return f"id:{oferta['id']}"
    return "txt:" + "|".join(normalizar_texto(oferta.get(c)) for c in ("titulo", "empresa", "ubicacion"))


def procesar_ofertas(ofertas: Any) -> List[Dict[str, Any]]:
    """
    Función principal del módulo. Recibe la lista del scraper y devuelve la
    lista lista para filtrar.

    Reglas:
      - Si la entrada no es una lista (None, texto, etc.) devuelve [].
      - Elementos que no son diccionarios se ignoran.
      - Una oferta sin título se descarta: sin título no se puede buscar.
      - Las ofertas repetidas (mismo id) se conservan una sola vez.
      - El resto de campos faltantes se mantienen como None.
    """
    if not isinstance(ofertas, list):
        return []

    resultado: List[Dict[str, Any]] = []
    vistas = set()

    for oferta in ofertas:
        if not isinstance(oferta, dict):
            continue
        limpia = limpiar_oferta(oferta)
        if not limpia["titulo"]:
            continue
        clave = _clave_duplicado(limpia)
        if clave in vistas:
            continue
        vistas.add(clave)
        resultado.append(limpia)

    return resultado


def contar_campos_faltantes(ofertas: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Informa cuántas ofertas tienen cada campo vacío (None).
    Sirve para explicar la calidad de los datos antes de filtrar.
    """
    return {
        campo: sum(1 for oferta in ofertas if not oferta.get(campo))
        for campo in CAMPOS_REVISADOS
    }


def cargar_ofertas_json(ruta: str = "ofertas_extraidas.json") -> List[Dict[str, Any]]:
    """
    Lee el archivo JSON que genera el Módulo 1. Si el archivo no existe o no
    contiene una lista válida devuelve [] en lugar de detener el programa.
    """
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return datos if isinstance(datos, list) else []


if __name__ == "__main__":
    # Demostración rápida: python procesador.py
    # Usa search.html (modo local) para no depender de la red.
    import logging

    from scraper import extraer_ofertas, obtener_html_archivo

    logging.disable(logging.CRITICAL)
    crudas = extraer_ofertas(obtener_html_archivo("search.html"))
    limpias = procesar_ofertas(crudas)

    print(f"Ofertas extraídas por el scraper : {len(crudas)}")
    print(f"Ofertas después de procesar      : {len(limpias)}")
    print(f"Campos faltantes                 : {contar_campos_faltantes(limpias)}")
    if limpias:
        print("\nEjemplo (antes → después):")
        print("  URL antes  :", crudas[0].get("url"))
        print("  URL después:", limpias[0]["url"])
        print("  Ubicación  :", limpias[0]["ubicacion"])
        print("  Separada   :", {c: limpias[0][c] for c in ("ciudad", "region", "pais")})
        print("  Normalizada:", normalizar_texto(limpias[0]["ubicacion"]))
