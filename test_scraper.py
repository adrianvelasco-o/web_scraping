"""
=============================================================================
SUITE DE PRUEBAS UNITARIAS — MÓDULO DE ADRIÁN VELASCO
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
    extraer_ofertas,
    extraer_titulo,
    extraer_empresa,
    extraer_ubicacion,
    extraer_fecha,
    extraer_url,
    extraer_id,
)


class TestModuloAdrian(unittest.TestCase):

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

        # Validar campos presentes y tipos
        self.assertIsNotNone(primera.get("titulo"), "El título no debe ser None")
        self.assertIsNotNone(primera.get("empresa"), "La empresa no debe ser None")
        self.assertIsNotNone(primera.get("ubicacion"), "La ubicación no debe ser None")
        self.assertIsNotNone(primera.get("fecha_publicacion"), "La fecha ISO no debe ser None")
        self.assertIsNotNone(primera.get("url"), "La URL no debe ser None")

        # Validaciones de formato
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
