# MÓDULO 2 — PROCESAMIENTO Y FILTRADO DE OFERTAS


**Módulo:** Limpieza + normalización + filtros
**Archivos:** `procesador.py`, `filtros.py`, `test_procesador.py`, `test_filtros.py`


## 1. Investigación

### 1.1 Procesamiento de datos
Los datos que salen de un scraper son *datos crudos*: están tal como aparecen en el HTML. Procesarlos es transformarlos en una forma confiable y uniforme antes de analizarlos. En este proyecto el procesamiento tiene tres etapas: limpieza, normalización y filtrado.

### 1.2 Limpieza
Limpiar es detectar y corregir errores e inconsistencias **sin cambiar lo que el dato significa**. Rahm y Do (2000) clasifican estos problemas en valores faltantes, formatos inconsistentes y registros duplicados, que son justamente los tres casos que maneja el módulo:

| Problema | Qué hace el módulo |
| :--- | :--- |
| Espacios repetidos, saltos de línea, espacio duro del HTML (`\xa0`) | Se reducen a un solo espacio |
| Valor vacío o que no es texto | Se convierte en `None` (nunca se inventa un valor) |
| URL con parámetros de seguimiento | Se conserva solo la dirección de la oferta |
| Fecha que no tiene formato `AAAA-MM-DD` | Se trata como dato faltante |
| Ofertas repetidas | Se conserva una sola por `id` |

### 1.3 Normalización
Normalizar es llevar valores que *significan lo mismo* a una **forma única** para poder compararlos. Para un programa, `"BOGOTÁ"`, `"Bogotá"` y `"bogota"` son tres cadenas diferentes. En recuperación de información esto se conoce como normalización de términos: pasar a minúsculas y eliminar diacríticos para que la consulta y el documento coincidan (Manning, Raghavan y Schütze, 2008, cap. 2).

Técnicas utilizadas:

* **`str.casefold()`**: conversión a minúsculas pensada para comparar textos sin distinguir mayúsculas (Python Software Foundation, s. f.-a).
* **Formas de normalización Unicode**: una letra con tilde puede escribirse como un solo carácter (`á`) o como dos (`a` + marca de tilde). La forma **NFC** las compone y la forma **NFD** las descompone (Unicode Consortium, 2024). El módulo usa NFC para limpiar y NFD para quitar las tildes: descompone y descarta los caracteres de categoría `Mn` (marcas).
* **Expresiones regulares** (`re.sub`) para cambiar la puntuación por espacios.

### 1.4 Parsing aplicado a los datos
El *parsing* no termina en el HTML. Un campo extraído también tiene estructura interna que se puede analizar:

* La ubicación `"Bogotá, Distrito Capital, Colombia"` se separa por comas en ciudad, región y país.
* La URL se descompone con `urllib.parse.urlsplit` en esquema, dominio, ruta y parámetros, y se reconstruye sin los parámetros.

### 1.5 Filtrado y búsqueda por palabras clave
Filtrar es seleccionar los registros que cumplen una condición. La búsqueda implementada es por **subcadena sobre texto normalizado**: una oferta coincide si la palabra buscada (normalizada) aparece dentro del título (normalizado). Los criterios se combinan con lógica booleana: **O** (`alguna`) e **Y** (`todas`).

---

## 2. Explicación del código

### 2.1 `procesador.py`

| Función | Qué hace |
| :--- | :--- |
| `limpiar_texto(valor)` | Quita espacios sobrantes y unifica Unicode (NFC). Devuelve `None` si está vacío o no es texto. |
| `limpiar_url(url)` | Elimina `?position=...&refId=...&trackingId=...`. Devuelve `None` si no es una URL http/https. |
| `limpiar_fecha(fecha)` | Acepta solo `AAAA-MM-DD`. |
| `normalizar_texto(valor)` | Minúsculas, sin tildes, sin puntuación. **Solo para comparar.** |
| `separar_ubicacion(ubicacion)` | Devuelve `ciudad`, `region`, `pais`. |
| `limpiar_oferta(oferta)` | Aplica todo lo anterior a una oferta, sin modificar la original. |
| `procesar_ofertas(ofertas)` | **Función principal.** Limpia la lista, descarta ofertas sin título y elimina duplicados. |
| `contar_campos_faltantes(ofertas)` | Cuántas ofertas tienen cada campo vacío. |
| `cargar_ofertas_json(ruta)` | Lee `ofertas_extraidas.json` generado por el Módulo 1. |

La función clave es `normalizar_texto`:

```python
def normalizar_texto(valor):
    texto = limpiar_texto(valor)
    if not texto:
        return ""
    texto = texto.casefold()                                  # "BOGOTÁ" → "bogotá"
    descompuesto = unicodedata.normalize("NFD", texto)        # "á" → "a" + tilde
    texto = "".join(c for c in descompuesto
                    if unicodedata.category(c) != "Mn")       # se descarta la tilde
    texto = re.sub(r"[^a-z0-9]+", " ", texto)                 # "d.c." → "d c"
    return texto.strip()
```

Estructura de una oferta procesada (los campos de Adrián más tres nuevos):

```json
{
  "id": "4487027152",
  "titulo": "Backend Engineer (Scala) - Remote Work | REF#290468",
  "empresa": "BairesDev",
  "ubicacion": "Bogotá, Distrito Capital, Colombia",
  "fecha_relativa": "Hace 1 semana",
  "fecha_publicacion": "2026-11-03",
  "url": "https://co.linkedin.com/jobs/view/...-4487027152",
  "ciudad": "Bogotá",
  "region": "Distrito Capital",
  "pais": "Colombia"
}
```

### 2.2 `filtros.py`

| Función | Qué hace |
| :--- | :--- |
| `coincide_palabra(oferta, palabra, campos, palabra_completa)` | Base de todos los filtros. `True` si la palabra o frase está en la oferta. |
| `filtrar_por_palabra(ofertas, palabra)` | Ofertas cuyo título contiene la palabra. |
| `filtrar_por_ubicacion(ofertas, ubicacion)` | Ofertas cuya ubicación contiene el texto. |
| `filtrar_por_varias_palabras(ofertas, palabras, modo)` | `modo="alguna"` (O) o `modo="todas"` (Y). |
| `filtrar_ofertas(ofertas, ubicacion, palabras, modo)` | Filtro combinado: ubicación y luego palabras. |
| `contar_por_palabra(ofertas, palabras)` | Diccionario `{palabra: cantidad}`. |
| `contar_varios_criterios(ofertas, palabras, minimo=2)` | Ofertas que cumplen dos o más palabras a la vez. |

Decisiones de diseño:

* La palabra buscada y el texto de la oferta pasan por **la misma** `normalizar_texto`. Por eso no importan mayúsculas ni tildes.
* Una palabra o ubicación **vacía no filtra** (devuelve todas las ofertas).
* Una oferta con el campo en `None` **nunca coincide y no produce error**.
* Los filtros devuelven listas nuevas; no modifican la lista original.
* Por defecto se busca solo en el título. Con `campos=("titulo", "empresa")` se incluye la empresa (ejemplo real: "scala" aparece en 2 títulos, pero también en la empresa *Scala Learning*, que no tiene relación con el lenguaje).

### 2.3 Uso

```python
from scraper import extraer_ofertas, obtener_html_archivo
from procesador import procesar_ofertas
from filtros import filtrar_ofertas, contar_por_palabra

ofertas = procesar_ofertas(extraer_ofertas(obtener_html_archivo("search.html")))
en_bogota = filtrar_ofertas(ofertas, ubicacion="Bogotá")
print(contar_por_palabra(en_bogota, ["Ingeniero", "Engineer", "Comercial"]))
```

Demostraciones desde consola (usan `search.html`, no requieren red):

```bash
python procesador.py
python filtros.py "Bogotá" "Ingeniero" "Atención al cliente" "Base de datos"
python filtros.py "Bogotá" Engineer Data Comercial
```

---

## 3. Pruebas

```bash
python -m unittest test_procesador test_filtros -v
```

57 pruebas, todas correctas (67 junto con las 10 del Módulo 1).

| Caso pedido en el plan | Dónde se prueba |
| :--- | :--- |
| Palabras inexistentes | `test_palabra_inexistente`, `test_ubicacion_inexistente` |
| Mayúsculas / minúsculas | `test_mayusculas_y_minusculas`, `test_tildes` |
| Datos vacíos | `test_limpiar_texto_datos_vacios`, `test_lista_vacia_o_none`, `test_ofertas_incompletas_no_generan_error` |
| Ubicación | clase `TestFiltroPorUbicacion` |
| Múltiples criterios | clase `TestCriteriosCombinados`, `test_contar_varios_criterios` |
| Resultados sin coincidencias | `test_combinacion_sin_coincidencias` |
| Integración scraper + procesamiento + filtros | `TestIntegracionConScraper`, `TestIntegracionFlujoCompleto` |

Las pruebas de filtros usan un conjunto pequeño de 6 ofertas inventadas **solo para pruebas**, donde el resultado esperado se puede contar a mano. Las pruebas de integración usan `search.html` y verifican propiedades (por ejemplo, que el resultado filtrado sea un subconjunto), no cantidades fijas, porque el archivo puede actualizarse.

---

## 4. Resultados sobre `search.html`

Obtenidos ejecutando el código sobre el archivo de referencia del repositorio (captura del 15 de noviembre de 2026). Si se descarga de nuevo la página, los números cambian.

| Medida | Resultado |
| :--- | ---: |
| Ofertas extraídas por el scraper | 60 |
| Ofertas después de procesar | 60 |
| Duplicados eliminados | 0 |
| Campos faltantes (id, título, empresa, ubicación, fecha, URL) | 0 |
| Textos corregidos por espacios repetidos | 1 título y 1 empresa |
| URLs a las que se quitaron parámetros de seguimiento | 60 |
| Ofertas en "Bogotá" | 53 |
| — "Bogotá, Distrito Capital, Colombia" | 47 |
| — "Área metropolitana de Bogotá D.C." | 6 |
| Ofertas fuera de Bogotá (Cundinamarca, Soacha, Tocancipá, Funza, Villavicencio) | 7 |

Palabras del enunciado, sobre las 53 ofertas de Bogotá (búsqueda en el título):

| Palabra clave | Ofertas |
| :--- | ---: |
| Ingeniero | 0 |
| Atención al cliente | 0 |
| Base de datos | 0 |
| Ofertas que cumplen varios criterios | 0 |

Otras palabras, sobre las mismas 53 ofertas:

| Palabra clave | Ofertas |
| :--- | ---: |
| Manager | 11 |
| Comercial | 9 |
| Engineer | 6 |
| Data | 3 |
| Engineer **y** Data (`modo="todas"`) | 3 |
| Engineer **o** Data (`modo="alguna"`) | 6 |

**Interpretación.** El cero de las tres palabras del enunciado no es un error del filtro. Tiene dos causas: (1) el listado público solo contiene el título de cada oferta, no su descripción; (2) muchos títulos están en inglés ("Engineer" en lugar de "Ingeniero").

---

## 5. Limitaciones del módulo

1. **Solo se busca en el título** (y opcionalmente en la empresa). La descripción no está en `search.html`.
2. **Búsqueda por subcadena.** "ti" aparece dentro de "Marketing". Para evitarlo existe `palabra_completa=True`.
3. **Sin sinónimos ni traducción.** "Ingeniero" no encuentra "Engineer".
4. **La "ñ" se compara como "n"** al quitar diacríticos ("año" y "ano" serían iguales). No afecta los datos actuales.
5. **Ubicación por texto.** "Soacha, Cundinamarca" no se cuenta como Bogotá aunque pertenezca a su área; el filtro no conoce geografía.
6. **Una sola página de resultados** (60 ofertas): los conteos describen esa muestra, no todo el mercado laboral.

