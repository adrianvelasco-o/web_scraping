# OBTENCIÓN Y EXTRACCIÓN DE OFERTAS LABORALES — LINKEDIN JOBS

Este repositorio contiene el módulo de Web Scraping sobre **LinkedIn Jobs** para la obtención y extracción estructurada de ofertas laborales.

---

## 1. Arquitectura del Proyecto

El proyecto está diseñado bajo una arquitectura modular desacoplada:

```text
      Módulo 1: Obtención y Extracción DOM
                       ↓
             ofertas_extraidas.json
                       ↓
   Módulo 2: Limpieza, Normalización y Filtros
                       ↓
   Módulo 3: Análisis de Datos y Métricas
```

---

## 2. Componentes del Módulo

* [`scraper.py`](file:///c:/Users/User/Documents/web_scraping/web_scraping/scraper.py): Script principal con técnicas de simulación de identidad humana, obtención en tiempo real y extracción estructurada.
* [`test_scraper.py`](file:///c:/Users/User/Documents/web_scraping/web_scraping/test_scraper.py): Suite de pruebas unitarias que valida las condiciones de robustez del scraper.
* [`requirements.txt`](file:///c:/Users/User/Documents/web_scraping/web_scraping/requirements.txt): Dependencias necesarias (`beautifulsoup4` y `requests`).
* [`ofertas_extraidas.json`](file:///c:/Users/User/Documents/web_scraping/web_scraping/ofertas_extraidas.json): Archivo generado con las ofertas extraídas para ser consumido en etapas posteriores.
* [`search.html`](file:///c:/Users/User/Documents/web_scraping/web_scraping/search.html): Archivo de referencia original para pruebas offline.

---

## 3. Parametrización por Ubicación y Simulación Humana

### A. Ubicación Configurable (Genérico y Reutilizable)
El scraper **no está limitado a una ubicación fija**. Puede consultar ofertas de cualquier ciudad o país sin modificar el código interno:
* La ubicación es un parámetro dinámico (`ubicacion="Bogotá"`, `ubicacion="Madrid"`, `ubicacion="Cali"`, `ubicacion="Nueva York"`, etc.).
* La función `construir_url_linkedin()` utiliza `urllib.parse.urlencode` (estándar RFC 3986) para codificar tildes (`Bogotá` → `Bogot%C3%A1`) y espacios (`Nueva York` → `Nueva+York`) de forma transparente.
* *Nota:* La ejecución inicial sobre España fue exclusivamente una prueba técnica de demostración. El scraper está parametrizado para cualquier ubicación.

### B. Técnicas de Simulación Humana
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

## 5. Estructura de Datos Estándar

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

## 6. Ejecución y Modos de Uso: Ubicación + Trabajo / Palabra Clave

El scraper permite realizar búsquedas combinadas mediante **Ubicación + Trabajo / Palabra clave**.

Principios de diseño:
* **Ubicación completamente libre:** No existen listas cerradas ni ciudades fijas. Se puede ingresar cualquier ciudad, región o país (ej. `Bogotá`, `Medellín`, `Cali`, `Pasto`, `Madrid`, `Barcelona`, `Nueva York`, `São Paulo`, `España`, `México`).
* **Trabajo / Palabra clave completamente libre:** Permite buscar cualquier cargo, tecnología o profesión (ej. `Ingeniero de software`, `Desarrollador Python`, `Backend Developer`, `Analista de datos`, `React`, `Java`).
* **Palabra clave opcional:** Si el usuario no ingresa palabra clave, el scraper recupera las vacantes generales para esa ubicación.
* **Codificación transparente:** Ambas cadenas se codifican de forma estándar con `urllib.parse.urlencode` soportando tildes (`Bogotá` → `Bogot%C3%A1`) y espacios (`Ingeniero de software` → `Ingeniero+de+software`).

### Opción 1 — Modo Interactivo en Consola
Al ejecutar el script sin argumentos, el sistema despliega el menú interactivo:
```bash
python scraper.py
```
Flujo en pantalla:
```text
========================================
       BUSCADOR DE OFERTAS DE EMPLEO
========================================

Ingrese la ubicación:
> Bogotá

Ingrese el trabajo o palabra clave:
> Ingeniero de software

Buscando ofertas de empleo...

Ubicación: Bogotá
Trabajo/palabra clave: Ingeniero de software
```
*(Nota: La ubicación es obligatoria; si se deja vacía, el programa la solicita de nuevo).*

### Opción 2 — Modo Línea de Comandos (CLI)
Permite pasar la ubicación y opcionalmente el trabajo directamente como argumentos:
```bash
# Ubicación + Trabajo / Palabra clave
python scraper.py "Bogotá" "Ingeniero de software"
python scraper.py "Medellín" "Python"
python scraper.py "Madrid" "Analista de datos"
python scraper.py "Nueva York" "Software Engineer"

# Búsqueda solo por ubicación (sin palabra clave)
python scraper.py "Cali"
python scraper.py "España"
```

### Opción 3 — Uso como Módulo desde Python
```python
from scraper import scrapear_ofertas

# Búsqueda combinada: ubicación + cargo
ofertas = scrapear_ofertas(
    ubicacion="Bogotá",
    palabras_clave="Ingeniero de software"
)

# Búsqueda solo por ubicación
ofertas_medellin = scrapear_ofertas(
    ubicacion="Medellín",
    palabras_clave="Python"
)
```

### Ejecutar las pruebas unitarias automatizadas:
```bash
python -m unittest discover -v
```

---

## 7. Guía Técnica para la Exposición

* **¿Qué es Web Scraping?** Técnica programática para extraer datos estructurados directamente del código HTML de un sitio web.
* **¿Diferencia con Web Crawling?** El *crawler* (rastreador) navega e indexa enlaces masivos por la red (como el bot de Google); el *scraper* entra a páginas puntuales para extraer datos específicos.
* **¿Qué es una petición HTTP?** Es el mensaje enviado desde nuestro cliente (script de Python) al servidor web solicitando un recurso (`GET`), recibiendo un código de estado (ej. `200 OK`).
* **¿Qué es el DOM?** Document Object Model: es la representación en árbol estructurado que los navegadores y librerías como BeautifulSoup construyen a partir del código HTML para permitir la búsqueda de elementos.
* **¿Cómo se maneja un dato faltante?** Se captura de forma defensiva con `select_one()` asignando `None`, evitando que una tarjeta incompleta interrumpa la extracción de las demás.
