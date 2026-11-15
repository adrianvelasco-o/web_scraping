"""
=============================================================================
PRUEBAS UNITARIAS — MÓDULO 2 (parte A): LIMPIEZA Y NORMALIZACIÓN
Responsable: Fanny
=============================================================================
Ejecutar:  python -m unittest test_procesador -v
=============================================================================
"""

import json
import logging
import os
import tempfile
import unittest

from procesador import (
    cargar_ofertas_json,
    contar_campos_faltantes,
    limpiar_fecha,
    limpiar_oferta,
    limpiar_texto,
    limpiar_url,
    normalizar_texto,
    procesar_ofertas,
    separar_ubicacion,
)

OFERTA_CRUDA = {
    "id": "4469750034",
    "titulo": "  Asesor comercial –  Cierre de Ventas\n",
    "empresa": "Scala\xa0Learning",
    "ubicacion": "Bogotá, Distrito Capital, Colombia",
    "fecha_publicacion": "2026-09-24",
    "fecha_relativa": "Hace 1 mes",
    "url": "https://co.linkedin.com/jobs/view/asesor-4469750034?position=1&trackingId=abc",
}


class TestLimpieza(unittest.TestCase):

    def test_limpiar_texto_quita_espacios_sobrantes(self):
        self.assertEqual(limpiar_texto("  Asesor   Comercial \n"), "Asesor Comercial")

    def test_limpiar_texto_espacio_duro_html(self):
        self.assertEqual(limpiar_texto("Scala\xa0Learning"), "Scala Learning")

    def test_limpiar_texto_conserva_mayusculas_y_tildes(self):
        """Limpiar no es normalizar: el texto visible no cambia."""
        self.assertEqual(limpiar_texto("Técnico De Mantenimiento"), "Técnico De Mantenimiento")

    def test_limpiar_texto_datos_vacios(self):
        for valor in (None, "", "    ", 123, [], {}):
            self.assertIsNone(limpiar_texto(valor), f"Debe ser None para {valor!r}")

    def test_limpiar_url_elimina_parametros_de_seguimiento(self):
        self.assertEqual(
            limpiar_url(OFERTA_CRUDA["url"]),
            "https://co.linkedin.com/jobs/view/asesor-4469750034",
        )

    def test_limpiar_url_invalida(self):
        for valor in (None, "", "no es una url", "javascript:alert(1)"):
            self.assertIsNone(limpiar_url(valor))

    def test_limpiar_fecha(self):
        self.assertEqual(limpiar_fecha("2026-11-03"), "2026-11-03")
        for valor in (None, "", "Hace 1 semana", "03/11/2026"):
            self.assertIsNone(limpiar_fecha(valor))


class TestNormalizacion(unittest.TestCase):

    def test_mayusculas_y_minusculas(self):
        self.assertEqual(normalizar_texto("INGENIERO"), normalizar_texto("ingeniero"))

    def test_tildes(self):
        self.assertEqual(normalizar_texto("Bogotá"), "bogota")
        self.assertEqual(normalizar_texto("Atención al Cliente"), "atencion al cliente")

    def test_puntuacion_y_espacios(self):
        self.assertEqual(normalizar_texto("Área metropolitana de Bogotá D.C."), "area metropolitana de bogota d c")
        self.assertEqual(normalizar_texto("Desarrollador/a   de Nuevos Negocios"), "desarrollador a de nuevos negocios")

    def test_datos_vacios_devuelven_cadena_vacia(self):
        for valor in (None, "", "   ", 42):
            self.assertEqual(normalizar_texto(valor), "")

    def test_separar_ubicacion_tres_partes(self):
        self.assertEqual(
            separar_ubicacion("Bogotá, Distrito Capital, Colombia"),
            {"ciudad": "Bogotá", "region": "Distrito Capital", "pais": "Colombia"},
        )

    def test_separar_ubicacion_dos_partes(self):
        self.assertEqual(
            separar_ubicacion("Cundinamarca, Colombia"),
            {"ciudad": None, "region": "Cundinamarca", "pais": "Colombia"},
        )

    def test_separar_ubicacion_una_parte(self):
        self.assertEqual(
            separar_ubicacion("Área metropolitana de Bogotá D.C."),
            {"ciudad": "Área metropolitana de Bogotá D.C.", "region": None, "pais": None},
        )

    def test_separar_ubicacion_vacia(self):
        self.assertEqual(separar_ubicacion(None), {"ciudad": None, "region": None, "pais": None})


class TestProcesarOfertas(unittest.TestCase):

    def test_limpiar_oferta_completa(self):
        limpia = limpiar_oferta(OFERTA_CRUDA)
        self.assertEqual(limpia["titulo"], "Asesor comercial – Cierre de Ventas")
        self.assertEqual(limpia["empresa"], "Scala Learning")
        self.assertEqual(limpia["ciudad"], "Bogotá")
        self.assertEqual(limpia["pais"], "Colombia")
        self.assertNotIn("?", limpia["url"])

    def test_limpiar_oferta_no_modifica_el_original(self):
        copia = dict(OFERTA_CRUDA)
        limpiar_oferta(OFERTA_CRUDA)
        self.assertEqual(OFERTA_CRUDA, copia)

    def test_campos_faltantes_quedan_en_none(self):
        limpia = limpiar_oferta({"titulo": "Analista"})
        self.assertEqual(limpia["titulo"], "Analista")
        for campo in ("id", "empresa", "ubicacion", "fecha_publicacion", "url", "ciudad"):
            self.assertIsNone(limpia[campo])

    def test_entrada_invalida_devuelve_lista_vacia(self):
        for entrada in (None, "texto", 5, {}):
            self.assertEqual(procesar_ofertas(entrada), [])
        self.assertEqual(procesar_ofertas([]), [])

    def test_descarta_elementos_invalidos_y_sin_titulo(self):
        entrada = [OFERTA_CRUDA, None, "basura", {"empresa": "Sin título S.A."}, {"titulo": "   "}]
        self.assertEqual(len(procesar_ofertas(entrada)), 1)

    def test_elimina_duplicados_por_id(self):
        repetida = dict(OFERTA_CRUDA, titulo="Asesor comercial – Cierre de Ventas")
        self.assertEqual(len(procesar_ofertas([OFERTA_CRUDA, repetida])), 1)

    def test_elimina_duplicados_sin_id(self):
        a = {"titulo": "Ejecutivo Comercial", "empresa": "ACME", "ubicacion": "Bogotá"}
        b = {"titulo": "EJECUTIVO  COMERCIAL", "empresa": "acme", "ubicacion": "bogota"}
        c = {"titulo": "Ejecutivo Comercial", "empresa": "Otra", "ubicacion": "Bogotá"}
        self.assertEqual(len(procesar_ofertas([a, b, c])), 2)

    def test_contar_campos_faltantes(self):
        ofertas = procesar_ofertas([OFERTA_CRUDA, {"titulo": "Analista"}])
        faltantes = contar_campos_faltantes(ofertas)
        self.assertEqual(faltantes["titulo"], 0)
        self.assertEqual(faltantes["empresa"], 1)
        self.assertEqual(faltantes["url"], 1)

    def test_cargar_json(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "ofertas.json")
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump([OFERTA_CRUDA], f, ensure_ascii=False)
            self.assertEqual(len(cargar_ofertas_json(ruta)), 1)

            with open(ruta, "w", encoding="utf-8") as f:
                f.write("{ esto no es json")
            self.assertEqual(cargar_ofertas_json(ruta), [])
        self.assertEqual(cargar_ofertas_json("archivo_que_no_existe.json"), [])


@unittest.skipUnless(os.path.exists("search.html"), "Requiere search.html")
class TestIntegracionConScraper(unittest.TestCase):
    """Scraper (Módulo 1) + procesamiento (Módulo 2) sobre el archivo de referencia."""

    @classmethod
    def setUpClass(cls):
        from scraper import extraer_ofertas, obtener_html_archivo

        logging.disable(logging.CRITICAL)
        cls.crudas = extraer_ofertas(obtener_html_archivo("search.html"))
        cls.limpias = procesar_ofertas(cls.crudas)
        logging.disable(logging.NOTSET)

    def test_no_se_pierden_ni_se_inventan_ofertas(self):
        self.assertGreater(len(self.limpias), 0)
        self.assertLessEqual(len(self.limpias), len(self.crudas))

    def test_ids_unicos(self):
        ids = [o["id"] for o in self.limpias if o["id"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_textos_sin_espacios_sobrantes(self):
        for oferta in self.limpias:
            for campo in ("titulo", "empresa", "ubicacion"):
                valor = oferta[campo]
                if valor is not None:
                    self.assertEqual(valor, valor.strip())
                    self.assertNotIn("  ", valor)

    def test_urls_sin_parametros(self):
        for oferta in self.limpias:
            if oferta["url"]:
                self.assertNotIn("?", oferta["url"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
