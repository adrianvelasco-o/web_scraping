"""
=============================================================================
PROYECTO DE WEB SCRAPING — LINKEDIN JOBS
MÓDULO 2 (parte B): FILTROS Y CONTEO DE COINCIDENCIAS
Responsable: Fanny
=============================================================================
Entrada : lista de ofertas (idealmente ya procesada con procesador.procesar_ofertas).
Salida  : sublistas de ofertas que cumplen los criterios y conteos por palabra.

Idea central (para la exposición):
  Tanto la palabra buscada como el texto de la oferta pasan por la MISMA
  función normalizar_texto(). Por eso "INGENIERO", "ingeniero" e "Ingeniéro"
  dan el mismo resultado, y "bogota" encuentra "Bogotá".

Limitación importante:
  El listado público (search.html) NO trae la descripción de la oferta.
  La búsqueda por palabra clave se hace sobre el TÍTULO (y, si se pide,
  sobre la empresa). Una oferta que mencione "base de datos" solo en su
  descripción no puede ser detectada.
=============================================================================
"""

from typing import Any, Dict, Iterable, List, Optional, Sequence

from procesador import normalizar_texto

# Campo donde se busca la palabra clave por defecto
CAMPOS_BUSQUEDA = ("titulo",)

# Campos donde se busca la ubicación
CAMPOS_UBICACION = ("ubicacion",)


# =============================================================================
# 1. COINCIDENCIA DE UNA OFERTA CON UN CRITERIO
# =============================================================================
def _texto_de_oferta(oferta: Any, campos: Sequence[str]) -> str:
    """Une y normaliza los campos indicados. Campos vacíos o None se ignoran."""
    if not isinstance(oferta, dict):
        return ""
    return " ".join(normalizar_texto(oferta.get(campo)) for campo in campos).strip()


def coincide_palabra(
    oferta: Dict[str, Any],
    palabra: str,
    campos: Sequence[str] = CAMPOS_BUSQUEDA,
    palabra_completa: bool = False,
) -> bool:
    """
    Indica si la oferta contiene la palabra o frase clave.

      - Sin distinguir mayúsculas, minúsculas ni tildes.
      - Una frase ("atención al cliente") debe aparecer completa y en ese orden.
      - palabra_completa=False (por defecto): "ingenier" encuentra "Ingeniero" e "Ingeniería".
      - palabra_completa=True: solo palabras enteras; "ti" NO coincide con "Marketing".
      - Una oferta sin datos en esos campos nunca coincide (no produce error).
    """
    buscada = normalizar_texto(palabra)
    texto = _texto_de_oferta(oferta, campos)
    if not buscada or not texto:
        return False
    if palabra_completa:
        return f" {buscada} " in f" {texto} "
    return buscada in texto


# =============================================================================
# 2. FILTROS
# =============================================================================
def filtrar_por_palabra(
    ofertas: Iterable[Dict[str, Any]],
    palabra: Optional[str],
    campos: Sequence[str] = CAMPOS_BUSQUEDA,
    palabra_completa: bool = False,
) -> List[Dict[str, Any]]:
    """
    Devuelve las ofertas que contienen la palabra clave.
    Si la palabra está vacía no se aplica filtro (se devuelven todas).
    """
    ofertas = list(ofertas or [])
    if not normalizar_texto(palabra):
        return ofertas
    return [o for o in ofertas if coincide_palabra(o, palabra, campos, palabra_completa)]


def filtrar_por_ubicacion(
    ofertas: Iterable[Dict[str, Any]],
    ubicacion: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Devuelve las ofertas cuya ubicación contiene el texto indicado.
    "bogota" encuentra "Bogotá, Distrito Capital, Colombia" y también
    "Área metropolitana de Bogotá D.C.".
    Si la ubicación está vacía no se aplica filtro. Las ofertas sin
    ubicación quedan fuera cuando sí se pide una.
    """
    ofertas = list(ofertas or [])
    if not normalizar_texto(ubicacion):
        return ofertas
    return [o for o in ofertas if coincide_palabra(o, ubicacion, CAMPOS_UBICACION)]


def filtrar_por_varias_palabras(
    ofertas: Iterable[Dict[str, Any]],
    palabras: Sequence[str],
    modo: str = "alguna",
    campos: Sequence[str] = CAMPOS_BUSQUEDA,
) -> List[Dict[str, Any]]:
    """
    Combina varias palabras clave.
      - modo="alguna": la oferta contiene AL MENOS UNA palabra (OR).
      - modo="todas" : la oferta contiene TODAS las palabras (AND).
    Las palabras vacías se ignoran; si no queda ninguna, no se filtra.
    """
    if modo not in ("alguna", "todas"):
        raise ValueError("modo debe ser 'alguna' o 'todas'")

    ofertas = list(ofertas or [])
    validas = [p for p in (palabras or []) if normalizar_texto(p)]
    if not validas:
        return ofertas

    combinar = any if modo == "alguna" else all
    return [o for o in ofertas if combinar(coincide_palabra(o, p, campos) for p in validas)]


def filtrar_ofertas(
    ofertas: Iterable[Dict[str, Any]],
    ubicacion: Optional[str] = None,
    palabras: Optional[Sequence[str]] = None,
    modo: str = "alguna",
) -> List[Dict[str, Any]]:
    """
    Filtro combinado: primero ubicación y después palabras clave.
    Ejemplo: filtrar_ofertas(ofertas, "Bogotá", ["engineer", "data"], modo="todas")
    """
    resultado = filtrar_por_ubicacion(ofertas, ubicacion)
    return filtrar_por_varias_palabras(resultado, palabras or [], modo)


# =============================================================================
# 3. CONTEO DE COINCIDENCIAS
# =============================================================================
def contar_por_palabra(
    ofertas: Iterable[Dict[str, Any]],
    palabras: Sequence[str],
    campos: Sequence[str] = CAMPOS_BUSQUEDA,
) -> Dict[str, int]:
    """
    Cuenta cuántas ofertas contienen cada palabra.
    Devuelve por ejemplo {"Ingeniero": 0, "Engineer": 7}.
    Una misma oferta puede contarse en varias palabras.
    """
    ofertas = list(ofertas or [])
    return {
        palabra: sum(1 for o in ofertas if coincide_palabra(o, palabra, campos))
        for palabra in (palabras or [])
    }


def contar_varios_criterios(
    ofertas: Iterable[Dict[str, Any]],
    palabras: Sequence[str],
    minimo: int = 2,
    campos: Sequence[str] = CAMPOS_BUSQUEDA,
) -> int:
    """
    Cuenta las ofertas que cumplen simultáneamente al menos 'minimo'
    palabras clave distintas (por defecto, dos o más).
    """
    validas = [p for p in (palabras or []) if normalizar_texto(p)]
    total = 0
    for oferta in list(ofertas or []):
        aciertos = sum(1 for p in validas if coincide_palabra(oferta, p, campos))
        if aciertos >= minimo:
            total += 1
    return total


if __name__ == "__main__":
    # Demostración: python filtros.py "Bogotá" "Ingeniero" "Atención al cliente" "Base de datos"
    # Trabaja sobre search.html (modo local) para que el resultado sea reproducible.
    import logging
    import sys

    from procesador import procesar_ofertas
    from scraper import extraer_ofertas, obtener_html_archivo

    logging.disable(logging.CRITICAL)

    ubicacion_demo = sys.argv[1] if len(sys.argv) > 1 else "Bogotá"
    palabras_demo = sys.argv[2:] or ["Ingeniero", "Atención al cliente", "Base de datos"]

    todas = procesar_ofertas(extraer_ofertas(obtener_html_archivo("search.html")))
    en_ubicacion = filtrar_por_ubicacion(todas, ubicacion_demo)

    print(f"Total de ofertas procesadas: {len(todas)}")
    print(f"Ofertas en \"{ubicacion_demo}\": {len(en_ubicacion)}\n")
    for palabra, cantidad in contar_por_palabra(en_ubicacion, palabras_demo).items():
        print(f"Ofertas relacionadas con \"{palabra}\": {cantidad}")
    print(f"\nOfertas que cumplen varios criterios: {contar_varios_criterios(en_ubicacion, palabras_demo)}")
