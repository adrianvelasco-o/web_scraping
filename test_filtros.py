"""
=============================================================================
PRUEBAS UNITARIAS — MÓDULO 2 (parte B): FILTROS Y CONTEO
Responsable: Fanny
=============================================================================
Casos pedidos en el plan del proyecto:
  - palabras inexistentes        - ubicación
  - mayúsculas / minúsculas      - múltiples criterios
  - datos vacíos                 - resultados sin coincidencias

Ejecutar:  python -m unittest test_filtros -v
=============================================================================
"""

import logging
import os
import unittest

from filtros import (
    coincide_palabra,
    contar_por_palabra,
    contar_varios_criterios,
    filtrar_ofertas,
    filtrar_por_palabra,
    filtrar_por_ubicacion,
    filtrar_por_varias_palabras,
)
from procesador import procesar_ofertas

# Conjunto pequeño y controlado: los resultados esperados se pueden contar a mano.
OFERTAS = [
    {"id": "1", "titulo": "Ingeniero de Datos", "empresa": "ACME",
     "ubicacion": "Bogotá, Distrito Capital, Colombia"},
    {"id": "2", "titulo": "Senior Data Engineer", "empresa": "Sezzle",
     "ubicacion": "Área metropolitana de Bogotá D.C."},
    {"id": "3", "titulo": "Asesor de Atención al Cliente", "empresa": "Scala Learning",
     "ubicacion": "Medellín, Antioquia, Colombia"},
    {"id": "4", "titulo": "ADMINISTRADOR DE BASE DE DATOS", "empresa": "Banco X",
     "ubicacion": "Bogotá, Distrito Capital, Colombia"},
    {"id": "5", "titulo": "Marketing Manager", "empresa": None, "ubicacion": None},
    {"id": "6", "titulo": "Ingeniero de Base de Datos", "empresa": "TI Global",
     "ubicacion": "Cali, Valle del Cauca, Colombia"},
]


def ids(ofertas):
    return [o["id"] for o in ofertas]


class TestFiltroPorPalabra(unittest.TestCase):

    def test_palabra_simple(self):
        self.assertEqual(ids(filtrar_por_palabra(OFERTAS, "Ingeniero")), ["1", "6"])

    def test_mayusculas_y_minusculas(self):
        esperado = ids(filtrar_por_palabra(OFERTAS, "ingeniero"))
        self.assertEqual(ids(filtrar_por_palabra(OFERTAS, "INGENIERO")), esperado)
        self.assertEqual(ids(filtrar_por_palabra(OFERTAS, "InGeNiErO")), esperado)

    def test_tildes(self):
        self.assertEqual(ids(filtrar_por_palabra(OFERTAS, "atencion al cliente")), ["3"])
        self.assertEqual(ids(filtrar_por_palabra(OFERTAS, "Atención al Cliente")), ["3"])

    def test_frase_completa(self):
        self.assertEqual(ids(filtrar_por_palabra(OFERTAS, "Base de datos")), ["4", "6"])
        # Las mismas palabras en otro orden no son la misma frase
        self.assertEqual(filtrar_por_palabra(OFERTAS, "datos de base"), [])

    def test_palabra_inexistente(self):
        self.assertEqual(filtrar_por_palabra(OFERTAS, "astronauta"), [])

    def test_palabra_vacia_no_filtra(self):
        for vacia in ("", "   ", None):
            self.assertEqual(len(filtrar_por_palabra(OFERTAS, vacia)), len(OFERTAS))

    def test_palabra_completa(self):
        # "ti" como parte de otra palabra: Marke-ti-ng
        self.assertTrue(coincide_palabra(OFERTAS[4], "ti"))
        self.assertFalse(coincide_palabra(OFERTAS[4], "ti", palabra_completa=True))

    def test_buscar_tambien_en_empresa(self):
        self.assertEqual(filtrar_por_palabra(OFERTAS, "scala"), [])
        self.assertEqual(ids(filtrar_por_palabra(OFERTAS, "scala", campos=("titulo", "empresa"))), ["3"])

    def test_el_filtro_no_modifica_la_lista_original(self):
        antes = [dict(o) for o in OFERTAS]
        filtrar_por_palabra(OFERTAS, "Ingeniero")
        self.assertEqual(OFERTAS, antes)


class TestFiltroPorUbicacion(unittest.TestCase):

    def test_ubicacion_con_y_sin_tilde(self):
        self.assertEqual(ids(filtrar_por_ubicacion(OFERTAS, "Bogotá")), ["1", "2", "4"])
        self.assertEqual(ids(filtrar_por_ubicacion(OFERTAS, "BOGOTA")), ["1", "2", "4"])

    def test_ubicacion_por_pais_o_region(self):
        self.assertEqual(ids(filtrar_por_ubicacion(OFERTAS, "Colombia")), ["1", "3", "4", "6"])
        self.assertEqual(ids(filtrar_por_ubicacion(OFERTAS, "Antioquia")), ["3"])

    def test_ubicacion_inexistente(self):
        self.assertEqual(filtrar_por_ubicacion(OFERTAS, "Tokio"), [])

    def test_oferta_sin_ubicacion_queda_fuera(self):
        self.assertNotIn("5", ids(filtrar_por_ubicacion(OFERTAS, "Bogotá")))

    def test_ubicacion_vacia_no_filtra(self):
        self.assertEqual(len(filtrar_por_ubicacion(OFERTAS, "")), len(OFERTAS))
        self.assertEqual(len(filtrar_por_ubicacion(OFERTAS, None)), len(OFERTAS))


class TestCriteriosCombinados(unittest.TestCase):

    def test_modo_alguna(self):
        resultado = filtrar_por_varias_palabras(OFERTAS, ["Ingeniero", "Base de datos"], modo="alguna")
        self.assertEqual(ids(resultado), ["1", "4", "6"])

    def test_modo_todas(self):
        resultado = filtrar_por_varias_palabras(OFERTAS, ["Ingeniero", "Base de datos"], modo="todas")
        self.assertEqual(ids(resultado), ["6"])

    def test_modo_invalido(self):
        with self.assertRaises(ValueError):
            filtrar_por_varias_palabras(OFERTAS, ["Ingeniero"], modo="otro")

    def test_ubicacion_mas_palabras(self):
        resultado = filtrar_ofertas(OFERTAS, ubicacion="Bogotá", palabras=["Ingeniero", "Engineer"])
        self.assertEqual(ids(resultado), ["1", "2"])

    def test_combinacion_sin_coincidencias(self):
        self.assertEqual(filtrar_ofertas(OFERTAS, ubicacion="Cali", palabras=["Atención al cliente"]), [])

    def test_sin_criterios_devuelve_todo(self):
        self.assertEqual(len(filtrar_ofertas(OFERTAS)), len(OFERTAS))


class TestConteo(unittest.TestCase):

    def test_contar_por_palabra(self):
        conteo = contar_por_palabra(OFERTAS, ["Ingeniero", "Atención al cliente", "Base de datos", "astronauta"])
        self.assertEqual(conteo, {"Ingeniero": 2, "Atención al cliente": 1, "Base de datos": 2, "astronauta": 0})

    def test_contar_varios_criterios(self):
        palabras = ["Ingeniero", "Atención al cliente", "Base de datos"]
        self.assertEqual(contar_varios_criterios(OFERTAS, palabras), 1)  # solo la oferta 6

    def test_conteo_coincide_con_el_filtro(self):
        for palabra in ("Ingeniero", "data", "manager", "nada"):
            self.assertEqual(
                contar_por_palabra(OFERTAS, [palabra])[palabra],
                len(filtrar_por_palabra(OFERTAS, palabra)),
            )


class TestDatosVaciosEIncompletos(unittest.TestCase):

    def test_lista_vacia_o_none(self):
        for entrada in ([], None):
            self.assertEqual(filtrar_por_palabra(entrada, "Ingeniero"), [])
            self.assertEqual(filtrar_por_ubicacion(entrada, "Bogotá"), [])
            self.assertEqual(contar_por_palabra(entrada, ["Ingeniero"]), {"Ingeniero": 0})
            self.assertEqual(contar_varios_criterios(entrada, ["a", "b"]), 0)

    def test_ofertas_incompletas_no_generan_error(self):
        incompletas = [{}, {"titulo": None}, {"titulo": ""}, {"empresa": "Solo empresa"}, None, "texto"]
        self.assertEqual(filtrar_por_palabra(incompletas, "Ingeniero"), [])
        self.assertEqual(filtrar_por_ubicacion(incompletas, "Bogotá"), [])


@unittest.skipUnless(os.path.exists("search.html"), "Requiere search.html")
class TestIntegracionFlujoCompleto(unittest.TestCase):
    """Scraper → procesamiento → filtros con los datos reales de search.html."""

    @classmethod
    def setUpClass(cls):
        from scraper import extraer_ofertas, obtener_html_archivo

        logging.disable(logging.CRITICAL)
        cls.ofertas = procesar_ofertas(extraer_ofertas(obtener_html_archivo("search.html")))
        logging.disable(logging.NOTSET)

    def test_filtrar_devuelve_subconjunto(self):
        en_bogota = filtrar_por_ubicacion(self.ofertas, "Bogotá")
        self.assertGreater(len(en_bogota), 0)
        self.assertLessEqual(len(en_bogota), len(self.ofertas))
        for oferta in en_bogota:
            self.assertIn(oferta, self.ofertas)

    def test_todas_las_filtradas_cumplen_el_criterio(self):
        for oferta in filtrar_por_ubicacion(self.ofertas, "bogota"):
            self.assertIn("bogot", oferta["ubicacion"].lower())

    def test_tilde_no_cambia_el_resultado(self):
        self.assertEqual(
            len(filtrar_por_ubicacion(self.ofertas, "Bogotá")),
            len(filtrar_por_ubicacion(self.ofertas, "BOGOTA")),
        )

    def test_modo_todas_nunca_supera_a_modo_alguna(self):
        palabras = ["engineer", "data"]
        todas = filtrar_por_varias_palabras(self.ofertas, palabras, modo="todas")
        alguna = filtrar_por_varias_palabras(self.ofertas, palabras, modo="alguna")
        self.assertLessEqual(len(todas), len(alguna))


if __name__ == "__main__":
    unittest.main(verbosity=2)
