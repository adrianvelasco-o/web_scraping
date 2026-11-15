# MÓDULO DE ADRIÁN VELASCO — OBTENCIÓN Y EXTRACCIÓN DE OFERTAS LABORALES

Este repositorio contiene el módulo inicial del proyecto académico de Web Scraping sobre **LinkedIn Jobs**, desarrollado por **Adrián Velasco**.

---

## 1. Arquitectura del Proyecto Académico

El proyecto está diseñado bajo una arquitectura modular desacoplada:

```text
       ADRIÁN (Este módulo)
  [Obtención + Extracción DOM]
              ↓
   ofertas_extraidas.json
              ↓
        FANNY (Módulo 2)
[Limpieza + Normalización + Filtros]
              ↓
        CAMILO (Módulo 3)
[Análisis + Métricas + Exposición]
```

---

## 2. Componentes del Módulo

* [`scraper.py`](file:///c:/Users/User/Documents/web_scraping/web_scraping/scraper.py): Script principal con técnicas de simulación de identidad humana, obtención en tiempo real y extracción estructurada.
* [`test_scraper.py`](file:///c:/Users/User/Documents/web_scraping/web_scraping/test_scraper.py): Suite de pruebas unitarias que valida las 6 condiciones de robustez exigidas.
* [`requirements.txt`](file:///c:/Users/User/Documents/web_scraping/web_scraping/requirements.txt): Dependencias necesarias (`beautifulsoup4` y `requests`).
* [`ofertas_extraidas.json`](file:///c:/Users/User/Documents/web_scraping/web_scraping/ofertas_extraidas.json): Archivo generado con las 60 ofertas extraídas en tiempo real para ser consumido por Fanny.
* [`search.html`](file:///c:/Users/User/Documents/web_scraping/web_scraping/search.html): Archivo de referencia original.

---

## 3. Técnicas de Simulación Humana Implementadas

Para evitar bloqueos de firewalls o detección como bot automatizado en LinkedIn, se implementaron las siguientes técnicas:

1. **Simulación de Identidad (Headers y User-Agent):**
   * Sustitución del `User-Agent` por defecto de Python por el de un navegador moderno: Google Chrome en Windows 11.
   * Inclusión de cabeceras de navegación realistas: `Accept-Language` (español), `Referer` (Google), `Sec-Ch-Ua`, `Sec-Fetch-*` y `Upgrade-Insecure-Requests`.
2. **Simulación de Frecuencia y Comportamiento:**
   * Pausas aleatorias con `random.uniform()` entre peticiones para imitar los tiempos de lectura y reacción de una persona real.
3. **Manejo de Errores y Códigos HTTP:**
   * Validación del código `200 OK`.
   * Detección y notificación clara de respuestas `429 Too Many Requests` o `403 Forbidden`.
   * Mecanismo de contingencia (*fallback*) automático hacia `search.html` si no hay conexión a internet.

---

## 4. Selectores CSS y Mapeo de Campos

Cada campo extraído corresponde a un selector real verificado:

| Campo | Selector CSS | Atributo / Método | Ejemplo Real |
| :--- | :--- | :--- | :--- |
| **Tarjeta contenedor** | `.job-search-card` | Elemento contenedor | `<li>` con tarjeta de empleo |
| **ID de oferta** | `[data-entity-urn]` | Atributo `data-entity-urn` | `4484678657` |
| **Título** | `h3.base-search-card__title` | Texto limpio | *"Encargado de tienda"* |
| **Empresa** | `h4.base-search-card__subtitle` | Texto limpio | *"Gamma Recruitment"* |
| **Ubicación** | `span.job-search-card__location` | Texto limpio | *"Badajoz"* |
| **Fecha ISO** | `time` | Atributo `datetime` | `2026-11-03` |
| **Fecha Relativa** | `time` | Texto interior | *"Hace 1 semana"* |
| **URL de la oferta** | `a.base-card__full-link` o `[href]` | Atributo `href` | `https://es.linkedin.com/jobs/view/...` |

---

## 5. Estructura de Datos Entregada a Fanny

```json
{
  "id": "4484678657",
  "titulo": "Encargado de tienda",
  "empresa": "Gamma Recruitment",
  "ubicacion": "Badajoz",
  "fecha_publicacion": "2026-11-03",
  "fecha_relativa": "Hace 1 semana",
  "url": "https://es.linkedin.com/jobs/view/encargado-de-tienda-at-gamma-recruitment-4484678657?position=1&pageNum=0&refId=wRRaGObw28dVPNI%2FspdL%2FA%3D%3D&trackingId=eSot4tWJvpLIbBhaFdYBDw%3D%3D"
}
```

---

## 6. Ejecución y Pruebas

### Ejecutar el scraper en tiempo real:
```bash
python scraper.py
```

### Ejecutar las pruebas unitarias:
```bash
python -m unittest test_scraper.py -v
```

---

## 7. Guía Rápida para la Exposición Universitaria de Adrián

* **¿Qué es Web Scraping?** Técnica programática para extraer datos estructurados directamente del código HTML de un sitio web.
* **¿Diferencia con Web Crawling?** El *crawler* (rastreador) navega e indexa enlaces masivos por la red (como el bot de Google); el *scraper* entra a páginas puntuales para extraer datos específicos.
* **¿Qué es una petición HTTP?** Es el mensaje enviado desde nuestro cliente (script de Python) al servidor web solicitando un recurso (`GET`), recibiendo un código de estado (ej. `200 OK`).
* **¿Qué es el DOM?** Document Object Model: es la representación en árbol estructurado que los navegadores y librerías como BeautifulSoup construyen a partir del código HTML para permitir la búsqueda de elementos.
* **¿Cómo se maneja un dato faltante?** Se captura de forma defensiva con `select_one()` asignando `None`, evitando que una tarjeta incompleta interrumpa la extracción de las demás.
