"""Candados de `mandar_correo`: lista blanca, tipos de adjunto, tope y armado del mensaje (sin tocar Gmail)."""

import tempfile
import unittest
from pathlib import Path

import servidor as s


class Destinatarios(unittest.TestCase):
    def test_normaliza_y_acepta_la_lista(self):
        p, c = s.validar_destinatarios([" FZajur@clearsky.com.ar "], ["hliguoro@clearsky.com.ar"])
        self.assertEqual((p, c), (["fzajur@clearsky.com.ar"], ["hliguoro@clearsky.com.ar"]))

    def test_uno_de_afuera_frena_todo(self):
        with self.assertRaises(s._Rechazado):
            s.validar_destinatarios(["fzajur@clearsky.com.ar", "otro@gmail.com"], [])

    def test_afuera_en_copia_tambien_frena(self):
        with self.assertRaises(s._Rechazado):
            s.validar_destinatarios(["fzajur@clearsky.com.ar"], ["fzajur@clearsky.com.ar.evil.com"])

    def test_sin_destinatarios(self):
        with self.assertRaises(s._Rechazado):
            s.validar_destinatarios(["", "  "], [])

    def test_no_se_cuela_con_nombre_y_direccion(self):
        with self.assertRaises(s._Rechazado):
            s.validar_destinatarios(["Fede <otro@gmail.com>"], [])


class Adjuntos(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def _archivo(self, nombre, tam=10):
        p = self.dir / nombre
        p.write_bytes(b"x" * tam)
        return str(p)

    def test_pdf_y_xlsx_pasan(self):
        self.assertEqual(len(s.validar_adjuntos([self._archivo("a.pdf"), self._archivo("b.XLSX")])), 2)

    def test_tipo_no_permitido(self):
        for nombre in (".env", "llave.dpapi", "datos.json", "x.exe", "sin_extension"):
            with self.assertRaises(s._Rechazado, msg=nombre):
                s.validar_adjuntos([self._archivo(nombre)])

    def test_inexistente(self):
        with self.assertRaises(s._Rechazado):
            s.validar_adjuntos([str(self.dir / "no.pdf")])

    def test_tope_de_tamano(self):
        viejo, s.TOPE_ADJUNTOS = s.TOPE_ADJUNTOS, 15
        try:
            with self.assertRaises(s._Rechazado):
                s.validar_adjuntos([self._archivo("a.pdf"), self._archivo("b.pdf")])
        finally:
            s.TOPE_ADJUNTOS = viejo


class Mensaje(unittest.TestCase):
    def test_arma_con_adjunto(self):
        d = Path(tempfile.mkdtemp())
        (d / "informe.pdf").write_bytes(b"%PDF-1.4")
        adj = s.validar_adjuntos([str(d / "informe.pdf")])
        m = s.armar_mensaje("jsmith@clearsky.com.ar", ["fzajur@clearsky.com.ar"], [], "Asunto", "Hola", adj)
        self.assertEqual(m["To"], "fzajur@clearsky.com.ar")
        self.assertEqual([a.get_filename() for a in m.iter_attachments()], ["informe.pdf"])

    def test_asunto_con_salto_de_linea(self):
        with self.assertRaises(s._Rechazado):
            s.armar_mensaje("a@b", ["fzajur@clearsky.com.ar"], [], "Hola\nBcc: otro@gmail.com", "x", [])

    def test_sin_texto(self):
        with self.assertRaises(s._Rechazado):
            s.armar_mensaje("a@b", ["fzajur@clearsky.com.ar"], [], "Asunto", "  ", [])


class Tope(unittest.TestCase):
    def test_frena_pasado_el_tope_sin_tocar_gmail(self):
        viejo, s._enviados = s._enviados, s.TOPE_ENVIOS
        try:
            r = s.mandar_correo(["fzajur@clearsky.com.ar"], "a", "b")
            self.assertIn("frené", r)
        finally:
            s._enviados = viejo


if __name__ == "__main__":
    unittest.main()
