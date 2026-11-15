"""
=============================================================================
SUITE DE PRUEBAS UNITARIAS — OBTENCIÓN Y EXTRACCIÓN DE OFERTAS
=============================================================================
Pruebas requeridas:
  Prueba 1 — Obtención: Carga correcta del HTML (local y manejo web).
  Prueba 2 — Identificación: Localización de las ofertas en el DOM.
  Prueba 3 — Extracción: Validación de campos (título, empresa, ubicación, fecha, url).
  Prueba 4 — Datos faltantes: Tolerancia a tarjetas con campos ausentes.
  Prueba 5 — HTML inesperado: Estructuras malformadas o ajenas no provocan caídas.
  Prueba 6 — Resultado vacío: Manejo de HTML sin ofertas devolviendo lista vacía [].
=============================================================================
"""

import os
import unittest
from bs4 import BeautifulSoup
from scraper import (
    obtener_html_archivo,
    normalizar_html,
    construir_url_linkedin,
    scrapear_ofertas,
    extraer_ofertas,
    extraer_titulo,
    extraer_empresa,
    extraer_ubicacion,
    extraer_fecha,
    extraer_url,
    extraer_id,
)


class TestScraper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Carga el archivo de referencia search.html una sola vez para las pruebas."""
        cls.ruta_search = "search.html"
        if os.path.exists(cls.ruta_search):
            cls.html_search = obtener_html_archivo(cls.ruta_search)
        else:
            cls.html_search = ""

    # -------------------------------------------------------------------------
    # PRUEBA 1 — OBTENCIÓN
    # -------------------------------------------------------------------------
    def test_01_obtencion_html_archivo(self):
        """Verifica que el contenido de referencia pueda obtenerse correctamente."""
        self.assertTrue(len(self.html_search) > 0, "El contenido de search.html no debe estar vacío")
        self.assertIn("line-content", self.html_search, "search.html debe contener las líneas exportadas")
        
        html_normalizado = normalizar_html(self.html_search)
        self.assertIn("job-search-card", html_normalizado, "El HTML normalizado debe contener las tarjetas laborales")

    # -------------------------------------------------------------------------
    # PRUEBA 2 — IDENTIFICACIÓN
    # -------------------------------------------------------------------------
    def test_02_identificacion_ofertas(self):
        """Verifica que se puedan localizar las ofertas en el DOM (60 ofertas)."""
        ofertas = extraer_ofertas(self.html_search)
        self.assertEqual(len(ofertas), 60, f"Se esperaban exactamente 60 ofertas, pero se hallaron {len(ofertas)}")

    # -------------------------------------------------------------------------
    # PRUEBA 3 — EXTRACCIÓN
    # -------------------------------------------------------------------------
    def test_03_extraccion_campos_completos(self):
        """Verifica que se extraigan correctamente los campos disponibles sin valores vacíos."""
        ofertas = extraer_ofertas(self.html_search)
        primera = ofertas[0]

        self.assertIsNotNone(primera.get("titulo"), "El título no debe ser None")
        self.assertIsNotNone(primera.get("empresa"), "La empresa no debe ser None")
        self.assertIsNotNone(primera.get("ubicacion"), "La ubicación no debe ser None")
        self.assertIsNotNone(primera.get("fecha_publicacion"), "La fecha ISO no debe ser None")
        self.assertIsNotNone(primera.get("url"), "La URL no debe ser None")

        self.assertTrue(primera["url"].startswith("http"), "La URL debe ser un enlace HTTP/HTTPS válido")
        self.assertEqual(len(primera["fecha_publicacion"].split("-")), 3, "La fecha debe tener formato YYYY-MM-DD")

    # -------------------------------------------------------------------------
    # PRUEBA 4 — DATOS FALTANTES
    # -------------------------------------------------------------------------
    def test_04_manejo_datos_faltantes(self):
        """Verifica que una oferta incompleta no rompa el proceso y asigne None."""
        html_incompleto = """
        <ul class="jobs-search__results-list">
            <li>
                <div class="base-card job-search-card">
                    <h3 class="base-search-card__title">Desarrollador Python Junior</h3>
                    <!-- Sin empresa, sin ubicacion, sin fecha, sin enlace -->
                </div>
            </li>
        </ul>
        """
        ofertas = extraer_ofertas(html_incompleto)
        self.assertEqual(len(ofertas), 1, "Debe procesar la oferta aunque le falten campos")
        of = ofertas[0]
        self.assertEqual(of["titulo"], "Desarrollador Python Junior")
        self.assertIsNone(of["empresa"], "La empresa faltante debe ser None")
        self.assertIsNone(of["ubicacion"], "La ubicación faltante debe ser None")
        self.assertIsNone(of["fecha_publicacion"], "La fecha faltante debe ser None")
        self.assertIsNone(of["url"], "La URL faltante debe ser None")

    # -------------------------------------------------------------------------
    # PRUEBA 5 — HTML INESPERADO
    # -------------------------------------------------------------------------
    def test_05_html_inesperado(self):
        """Verifica el comportamiento ante una estructura que no coincida con lo esperado."""
        html_ajeno = """
        <html>
            <head><title>Página de error</title></head>
            <body>
                <h1>404 No Encontrado</h1>
                <p>El recurso solicitado no existe en este servidor.</p>
            </body>
        </html>
        """
        ofertas = extraer_ofertas(html_ajeno)
        self.assertIsInstance(ofertas, list, "Debe retornar una lista")
        self.assertEqual(len(ofertas), 0, "No debe encontrar ofertas en un HTML ajeno")

    # -------------------------------------------------------------------------
    # PRUEBA 6 — RESULTADO VACÍO
    # -------------------------------------------------------------------------
    def test_06_resultado_vacio(self):
        """Verifica qué sucede cuando se pasa un HTML vacío o en blanco."""
        self.assertEqual(extraer_ofertas(""), [], "Cadena vacía debe retornar lista vacía")
        self.assertEqual(extraer_ofertas("   \n\t  "), [], "Espacios en blanco deben retornar lista vacía")
        self.assertEqual(extraer_ofertas(None), [], "None debe retornar lista vacía")

    # -------------------------------------------------------------------------
    # PRUEBA 7 — CONSTRUCCIÓN DE URL PARAMETRIZABLE (DIVERSAS UBICACIONES)
    # -------------------------------------------------------------------------
    def test_07_construccion_url_parametrizable(self):
        """Verifica que la URL se construya dinámicamente según la ubicación libre y codifique caracteres especiales."""
        # Prueba con tildes (Bogotá, Medellín)
        url_bogota = construir_url_linkedin(ubicacion="Bogotá")
        self.assertIn("location=Bogot%C3%A1", url_bogota, "Bogotá debe codificar la tilde a %C3%A1")
        self.assertIn("https://es.linkedin.com/jobs/search", url_bogota)

        url_medellin = construir_url_linkedin(ubicacion="Medellín")
        self.assertIn("location=Medell%C3%ADn", url_medellin, "Medellín debe codificar la tilde a %C3%AD")

        # Prueba con ubicación estándar simple (Madrid, Cali, Pasto)
        url_madrid = construir_url_linkedin(ubicacion="Madrid")
        self.assertIn("location=Madrid", url_madrid)

        url_pasto = construir_url_linkedin(ubicacion="Pasto")
        self.assertIn("location=Pasto", url_pasto)

        # Prueba con espacios y caracteres internacionales (Nueva York, São Paulo)
        url_ny = construir_url_linkedin(ubicacion="Nueva York")
        self.assertIn("location=Nueva+York", url_ny, "Espacios deben codificarse a + o %20")

        url_sp = construir_url_linkedin(ubicacion="São Paulo")
        self.assertIn("location=S%C3%A3o+Paulo", url_sp, "Caracteres como ã deben codificarse según UTF-8")

        # Prueba combinada con palabras clave
        url_con_keywords = construir_url_linkedin(ubicacion="Cali", palabras_clave="Ingeniero de software")
        self.assertIn("keywords=Ingeniero+de+software", url_con_keywords)
        self.assertIn("location=Cali", url_con_keywords)

    # -------------------------------------------------------------------------
    # PRUEBA 8 — PUNTO DE ENTRADA scrapear_ofertas
    # -------------------------------------------------------------------------
    def test_08_scrapear_ofertas_modo_local(self):
        """Verifica que la función genérica scrapear_ofertas funcione en modo local de respaldo."""
        ofertas = scrapear_ofertas(ubicacion="Medellín", modo="local", guardar_json=False)
        self.assertIsInstance(ofertas, list)
        self.assertEqual(len(ofertas), 60, "Debe procesar las 60 ofertas en modo local")
        self.assertIsNotNone(ofertas[0]["titulo"])

    # -------------------------------------------------------------------------
    # PRUEBA 9 — CONSISTENCIA DE ESTRUCTURA Y CAMPOS
    # -------------------------------------------------------------------------
    def test_09_consistencia_campos_estructura(self):
        """Valida que cada oferta mantenga exactamente las 7 claves esperadas."""
        ofertas = scrapear_ofertas(ubicacion="Bogotá", modo="local", guardar_json=False)
        claves_esperadas = {"id", "titulo", "empresa", "ubicacion", "fecha_publicacion", "fecha_relativa", "url"}
        for oferta in ofertas:
            self.assertEqual(set(oferta.keys()), claves_esperadas, "Las claves del diccionario deben ser exactas")

    # -------------------------------------------------------------------------
    # PRUEBA 10 — BÚSQUEDA COMBINADA: UBICACIÓN + TRABAJO / PALABRA CLAVE
    # -------------------------------------------------------------------------
    def test_10_busqueda_combinada_ubicacion_trabajo(self):
        """Verifica la construcción de URLs combinando ubicación y cargo/tecnología."""
        # Caso 1: Bogotá + Ingeniero de software
        url_1 = construir_url_linkedin("Bogotá", "Ingeniero de software")
        self.assertIn("location=Bogot%C3%A1", url_1)
        self.assertIn("keywords=Ingeniero+de+software", url_1)

        # Caso 2: Nueva York + Python
        url_2 = construir_url_linkedin("Nueva York", "Python")
        self.assertIn("location=Nueva+York", url_2)
        self.assertIn("keywords=Python", url_2)

        # Caso 3: Madrid + Analista de datos
        url_3 = construir_url_linkedin("Madrid", "Analista de datos")
        self.assertIn("location=Madrid", url_3)
        self.assertIn("keywords=Analista+de+datos", url_3)

        # Caso 4: São Paulo + Ingeniería de software (tildes combinadas)
        url_4 = construir_url_linkedin("São Paulo", "Ingeniería de software")
        self.assertIn("location=S%C3%A3o+Paulo", url_4)
        self.assertIn("keywords=Ingenier%C3%ADa+de+software", url_4)

        # Caso 5: Ubicación sin palabra clave (palabra clave opcional)
        url_5 = construir_url_linkedin("Medellín", "")
        self.assertIn("location=Medell%C3%ADn", url_5)
        self.assertIn("keywords=", url_5)

        # Caso 6: Ejecución completa en modo local con ambos parámetros
        ofertas = scrapear_ofertas(
            ubicacion="Bogotá",
            palabras_clave="Ingeniero de software",
            modo="local",
            guardar_json=False,
        )
        self.assertEqual(len(ofertas), 60)
        self.assertEqual(
            set(ofertas[0].keys()),
            {"id", "titulo", "empresa", "ubicacion", "fecha_publicacion", "fecha_relativa", "url"},
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
