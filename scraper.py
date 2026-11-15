"""
=============================================================================
PROYECTO ACADÉMICO DE WEB SCRAPING — LINKEDIN JOBS
MÓDULO DE ADRIÁN VELASCO: OBTENCIÓN Y EXTRACCIÓN DE OFERTAS
=============================================================================

Responsabilidad de Adrián:
  1. OBTENCIÓN: Simular identidad humana (cabeceras, User-Agent, pausas) y
     realizar la petición HTTP a la fuente web (o cargar archivo de respaldo).
  2. PARSEO Y SELECTORES: Analizar el árbol DOM con BeautifulSoup.
  3. EXTRACCIÓN: Localizar tarjetas laborales y extraer campos estructurados.
  4. ENTREGA: Producir una lista de ofertas limpias para el módulo de Fanny
     (limpieza, normalización y filtros).
=============================================================================
"""

import json
import logging
import random
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

# Configuración básica de logging para seguimiento claro durante la ejecución
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ScraperAdrian")

# URL objetivo en tiempo real (Empleos en España / LinkedIn público)
URL_OBJETIVO_DEFAULT = (
    "https://es.linkedin.com/jobs/search/"
    "?lipi=urn%3Ali%3Apage%3Ad_homepage-guest-home_jsbeacon%3BNjGI0v8QTPm9uHLYtxyPbA%3D%3D"
    "&position=1&pageNum=0"
)


# =============================================================================
# 1. TÉCNICAS DE SIMULACIÓN DE IDENTIDAD HUMANA (HEADERS Y CLIENTE HTTP)
# =============================================================================
def obtener_cabeceras_navegador() -> Dict[str, str]:
    """
    Construye cabeceras HTTP que imitan fielmente a un navegador real (Chrome en Windows).

    Explicación técnica para la exposición:
    --------------------------------------
    1. User-Agent: Las librerías como 'requests' o 'urllib' envían por defecto
       'python-requests/2.X', lo cual es bloqueado de inmediato por los WAF
       (Web Application Firewalls). Aquí enviamos la firma de Google Chrome 133.
    2. Accept: Indica qué formatos visuales comprende el cliente (HTML, WebP, etc.).
    3. Accept-Language: Prioriza el idioma español (es-ES, es), imitando a un
       usuario hispanohablante.
    4. Sec-Ch-Ua / Sec-Fetch: Cabeceras modernas de seguridad del navegador
       (Client Hints) que diferencian tráfico humano legítimo de scripts básicos.
    5. Referer: Simula que el usuario llegó a través del buscador Google.
    """
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/133.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://www.google.com/",
        "Sec-Ch-Ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Connection": "keep-alive",
    }


# =============================================================================
# 2. SIMULACIÓN DE COMPORTAMIENTO Y FRECUENCIA
# =============================================================================
def aplicar_pausa_humana(min_seg: float = 1.5, max_seg: float = 3.5) -> None:
    """
    Introduce una pausa aleatoria para imitar el tiempo de reacción humano.

    Explicación técnica para la exposición:
    --------------------------------------
    Los servidores monitorean la cadencia de peticiones. Las máquinas suelen
    consultar con intervalos idénticos y a velocidades inhumanas (ej. 50 ms).
    Introducir variación estocástica (random.uniform) rompe patrones predecibles
    y evita la activación de algoritmos de 'rate-limiting'.
    """
    espera = round(random.uniform(min_seg, max_seg), 2)
    logger.info(f"Simulando pausa de lectura humana: {espera} segundos...")
    time.sleep(espera)


# =============================================================================
# 3. OBTENCIÓN DEL HTML (RED O RESPALDO LOCAL)
# =============================================================================
def obtener_html_web(url: str = URL_OBJETIVO_DEFAULT, timeout: int = 15) -> str:
    """
    Realiza una petición HTTP GET segura a la URL en tiempo real.

    Manejo de Errores:
    - Valida código 200 OK.
    - Notifica explícitamente si ocurre un 429 (Too Many Requests) o 403 (Forbidden).
    - Captura excepciones de conexión o tiempo de espera.
    """
    aplicar_pausa_humana(1.0, 2.5)
    headers = obtener_cabeceras_navegador()

    logger.info(f"Conectando a LinkedIn Jobs en tiempo real: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=timeout)

        if response.status_code == 200:
            logger.info(f"Petición exitosa [200 OK]. Tamaño recibido: {len(response.text):,} caracteres.")
            return response.text
        elif response.status_code == 429:
            logger.warning("Respuesta HTTP 429: Límite de peticiones alcanzado en LinkedIn.")
            raise requests.HTTPError(f"HTTP 429 Too Many Requests: {response.reason}")
        elif response.status_code == 403:
            logger.warning("Respuesta HTTP 403: Acceso denegado o validación antibot.")
            raise requests.HTTPError(f"HTTP 403 Forbidden: {response.reason}")
        else:
            response.raise_for_status()
            return response.text

    except requests.exceptions.RequestException as e:
        logger.error(f"Error durante la conexión HTTP: {e}")
        raise


def obtener_html_archivo(ruta_archivo: str = "search.html") -> str:
    """
    Carga el contenido HTML desde un archivo local de referencia.
    Útil para pruebas offline, desarrollo y contingencia.
    """
    logger.info(f"Cargando HTML de referencia local desde: {ruta_archivo}")
    try:
        with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Archivo no encontrado: {ruta_archivo}")
        raise


def normalizar_html(html_crudo: str) -> str:
    """
    Garantiza que el HTML sea procesable sin importar su origen.

    Si el archivo fue guardado desde 'view-source:' de Chrome (como search.html),
    el código HTML real está contenido dentro de celdas '<td class="line-content">'.
    Esta función detecta dicha condición y reconstruye el HTML puro.
    Si ya es HTML estándar devuelto por HTTP, lo retorna tal cual.
    """
    if not html_crudo or not html_crudo.strip():
        return ""

    if '<td class="line-content">' in html_crudo:
        logger.info("Detectado formato view-source de Chrome. Reconstruyendo DOM puro...")
        soup_wrapper = BeautifulSoup(html_crudo, "html.parser")
        lineas = soup_wrapper.find_all("td", class_="line-content")
        return "\n".join(td.get_text() for td in lineas)

    return html_crudo


# =============================================================================
# 4. SELECTORES Y FUNCIONES ATÓMICAS DE EXTRACCIÓN
# =============================================================================
def extraer_titulo(tarjeta: Tag) -> Optional[str]:
    """
    Selector: 'h3.base-search-card__title'
    Extrae el título del puesto de trabajo publicado.
    """
    elem = tarjeta.select_one("h3.base-search-card__title")
    if elem:
        texto = elem.get_text(strip=True)
        return texto if texto else None
    return None


def extraer_empresa(tarjeta: Tag) -> Optional[str]:
    """
    Selector: 'h4.base-search-card__subtitle'
    Extrae el nombre de la empresa contratante.
    """
    elem = tarjeta.select_one("h4.base-search-card__subtitle")
    if elem:
        texto = elem.get_text(strip=True)
        return texto if texto else None
    return None


def extraer_ubicacion(tarjeta: Tag) -> Optional[str]:
    """
    Selector: 'span.job-search-card__location'
    Extrae la ciudad, región o país de la vacante.
    """
    elem = tarjeta.select_one("span.job-search-card__location")
    if elem:
        texto = elem.get_text(strip=True)
        return texto if texto else None
    return None


def extraer_fecha(tarjeta: Tag) -> Dict[str, Optional[str]]:
    """
    Selector: 'time' (clases .job-search-card__listdate o .job-search-card__listdate--new)
    Extrae:
      - fecha_publicacion: Fecha estándar de máquina en formato ISO (atributo 'datetime', ej: 2026-11-12)
      - fecha_relativa: Antigüedad expresada en lenguaje natural (ej: 'Hace 3 días', 'Hace 2 horas')
    """
    elem = tarjeta.select_one("time")
    if elem:
        datetime_val = elem.get("datetime")
        texto_relativo = elem.get_text(strip=True)
        return {
            "fecha_publicacion": datetime_val if datetime_val else None,
            "fecha_relativa": texto_relativo if texto_relativo else None,
        }
    return {"fecha_publicacion": None, "fecha_relativa": None}


def extraer_url(tarjeta: Tag) -> Optional[str]:
    """
    Selector: 'a.base-card__full-link' o atributo 'href' directo en la tarjeta.
    Extrae la URL pública que dirige a la oferta completa.
    """
    # Caso 1: Enlace interno completo
    enlace = tarjeta.select_one("a.base-card__full-link")
    if enlace and enlace.get("href"):
        return enlace.get("href").strip()

    # Caso 2: La tarjeta misma es una etiqueta <a>
    if tarjeta.name == "a" and tarjeta.get("href"):
        return tarjeta.get("href").strip()

    # Caso 3: Fallback a cualquier hipervínculo interno hacia un empleo
    enlace_fallback = tarjeta.select_one("a[href*='/jobs/view/']")
    if enlace_fallback and enlace_fallback.get("href"):
        return enlace_fallback.get("href").strip()

    return None


def extraer_id(tarjeta: Tag) -> Optional[str]:
    """
    Atributo: 'data-entity-urn' (ej. 'urn:li:jobPosting:4388211075')
    Extrae el identificador numérico único de LinkedIn para evitar duplicados.
    """
    urn = tarjeta.get("data-entity-urn")
    if urn and "jobPosting:" in urn:
        return urn.split("jobPosting:")[-1].strip()
    return None


# =============================================================================
# 5. PARSER PRINCIPAL DE EXTRACCIÓN
# =============================================================================
def extraer_ofertas(html: str) -> List[Dict[str, Any]]:
    """
    Recibe una cadena HTML, analiza el DOM y devuelve una lista de diccionarios
    con cada una de las ofertas encontradas.

    Estructura de salida entregada a Fanny:
    [
        {
            "id": "4484678657",
            "titulo": "Encargado de tienda",
            "empresa": "Gamma Recruitment",
            "ubicacion": "Badajoz",
            "fecha_publicacion": "2026-11-03",
            "fecha_relativa": "Hace 1 semana",
            "url": "https://es.linkedin.com/jobs/view/..."
        },
        ...
    ]
    """
    if not html or not html.strip():
        logger.warning("El HTML proporcionado está vacío.")
        return []

    # Normalizar en caso de que sea formato view-source de Chrome
    html_limpio = normalizar_html(html)

    # Parsear árbol DOM con html.parser (nativo de Python)
    soup = BeautifulSoup(html_limpio, "html.parser")

    # Localizar las tarjetas de empleo con el selector unificado
    tarjetas = soup.select(".job-search-card")

    if not tarjetas:
        # Intento de selector alternativo en caso de ligeras variaciones de plantilla
        tarjetas = soup.select("ul.jobs-search__results-list > li")

    logger.info(f"Tarjetas de empleo localizadas en el DOM: {len(tarjetas)}")

    ofertas_extraidas: List[Dict[str, Any]] = []

    for index, tarjeta in enumerate(tarjetas, start=1):
        try:
            titulo = extraer_titulo(tarjeta)
            empresa = extraer_empresa(tarjeta)
            ubicacion = extraer_ubicacion(tarjeta)
            datos_fecha = extraer_fecha(tarjeta)
            url_oferta = extraer_url(tarjeta)
            job_id = extraer_id(tarjeta)

            # Si la tarjeta no contiene ni título ni empresa, se descarta (posible elemento decorativo)
            if not titulo and not empresa:
                continue

            oferta: Dict[str, Any] = {
                "id": job_id,
                "titulo": titulo,
                "empresa": empresa,
                "ubicacion": ubicacion,
                "fecha_publicacion": datos_fecha["fecha_publicacion"],
                "fecha_relativa": datos_fecha["fecha_relativa"],
                "url": url_oferta,
            }

            ofertas_extraidas.append(oferta)

        except Exception as err:
            # Tolerancia ante fallos: una tarjeta corrupta no interrumpe el resto del scraping
            logger.warning(f"Error extrayendo tarjeta #{index}: {err}")
            continue

    logger.info(f"Total de ofertas estructuradas con éxito: {len(ofertas_extraidas)}")
    return ofertas_extraidas


# =============================================================================
# 6. FUNCIÓN DE PRESENTACIÓN Y FLUJO COMPLETO
# =============================================================================
def mostrar_resumen_ofertas(ofertas: List[Dict[str, Any]], limite: int = 10) -> None:
    """
    Imprime en consola el reporte formateado según las especificaciones del proyecto.
    """
    print("\n" + "=" * 70)
    print(f"OFERTAS ENCONTRADAS: {len(ofertas)}")
    print("=" * 70)

    for i, of in enumerate(ofertas[:limite], start=1):
        print(f"\nOferta {i}")
        print(f"ID:        {of.get('id')}")
        print(f"Título:    {of.get('titulo')}")
        print(f"Empresa:   {of.get('empresa')}")
        print(f"Ubicación: {of.get('ubicacion')}")
        print(f"Fecha:     {of.get('fecha_publicacion')} ({of.get('fecha_relativa')})")
        print(f"URL:       {of.get('url')}")

    if len(ofertas) > limite:
        print(f"\n... y {len(ofertas) - limite} ofertas más disponibles en el conjunto de datos.")
    print("=" * 70 + "\n")


def ejecutar_scraping(
    modo: str = "web",
    url: str = URL_OBJETIVO_DEFAULT,
    ruta_archivo: str = "search.html",
    guardar_json: bool = True,
    archivo_salida: str = "ofertas_extraidas.json",
) -> List[Dict[str, Any]]:
    """
    Función de orquestación principal del Módulo de Adrián.

    Parámetros:
      - modo: 'web' para scraping en tiempo real, 'local' para search.html.
      - url: Dirección web de LinkedIn Jobs a consultar.
      - ruta_archivo: Ruta al archivo local de respaldo.
      - guardar_json: Si es True, almacena los resultados para que Fanny los use.
      - archivo_salida: Nombre del archivo JSON a generar.
    """
    logger.info(f"Iniciando Módulo de Obtención y Extracción (Modo: '{modo}')")

    if modo == "web":
        try:
            html = obtener_html_web(url=url)
        except Exception as e:
            logger.warning(f"Fallo en la petición web ({e}). Activando fallback a archivo local...")
            html = obtener_html_archivo(ruta_archivo=ruta_archivo)
    else:
        html = obtener_html_archivo(ruta_archivo=ruta_archivo)

    # Extracción de ofertas
    ofertas = extraer_ofertas(html)

    # Presentación
    mostrar_resumen_ofertas(ofertas)

    # Guardar para entrega limpia a Fanny
    if guardar_json and ofertas:
        with open(archivo_salida, "w", encoding="utf-8") as f:
            json.dump(ofertas, f, ensure_ascii=False, indent=2)
        logger.info(f"Datos estructurados guardados en '{archivo_salida}' para el Módulo de Fanny.")

    return ofertas


if __name__ == "__main__":
    # Ejecución por defecto en tiempo real a la URL solicitada
    ejecutar_scraping(modo="web")
