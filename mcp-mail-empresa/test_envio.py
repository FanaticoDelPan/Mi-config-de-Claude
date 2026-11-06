"""Candados de `mandar_correo`, de punta a punta con un Gmail FALSO.

🔴 Ningún test puede llegar al Gmail real: el pase de envío vive en el perfil (no en el repo), así que mutar el
código en otra carpeta no protege. `setUpModule` reemplaza el servicio por uno que falla y apunta LOCALAPPDATA a
una carpeta temporal; cada test que necesita mandar instala su propio falso que captura el mensaje.
"""

import email
import os
import tempfile
import threading
import time
import unittest
from email import policy
from pathlib import Path
from unittest import mock

import servidor as s

_parches = []


class _Prohibido(AssertionError):
    pass


def _nunca():
    raise _Prohibido("un test intentó usar el Gmail real")


LISTA_DE_PRUEBA = """\
# comentario
socio@empresa.test        # un socio
colega@empresa.test
yo@empresa.test
yo.personal@personal.test   solo-texto
renglon sin arroba
"""


def setUpModule():
    tmp = tempfile.mkdtemp()
    lista = Path(tmp) / "lista-blanca.txt"
    lista.write_text(LISTA_DE_PRUEBA, encoding="utf-8")
    todas, solo_texto = s.cargar_lista(lista)
    for p in (mock.patch.dict(os.environ, {"LOCALAPPDATA": tmp}), mock.patch.object(s, "_gmail_envio", _nunca),
              mock.patch.object(s, "_mandar", lambda *a: _nunca()),
              mock.patch.object(s, "LISTA_BLANCA", todas), mock.patch.object(s, "SOLO_SIN_ADJUNTOS", solo_texto)):
        p.start()
        _parches.append(p)


def tearDownModule():
    for p in reversed(_parches):
        p.stop()


class _Falso:
    """Reemplaza el servicio y el envío: guarda cada mensaje mandado."""

    def __init__(self, demora=0.0):
        self.mandados, self.demora = [], demora

    def __enter__(self):
        s._enviados = 0
        self._p = [mock.patch.object(s, "_gmail_envio", lambda: ("yo@empresa.test", object())),
                   mock.patch.object(s, "_mandar", self._mandar)]
        for p in self._p:
            p.start()
        return self

    def _mandar(self, _gmail, mensaje):
        time.sleep(self.demora)
        self.mandados.append(email.message_from_bytes(mensaje.as_bytes(), policy=policy.default))
        return f"id{len(self.mandados)}"

    def __exit__(self, *_):
        for p in self._p:
            p.stop()
        s._enviados = 0


def _registro():
    archivo = s.boveda.carpeta() / "enviados.log"
    return archivo.read_text(encoding="utf-8").splitlines() if archivo.exists() else []


def _pdf(nombre="informe.pdf", tam=10):
    p = Path(tempfile.mkdtemp()) / nombre
    p.write_bytes(b"x" * tam)
    return str(p)


class PuntaAPunta(unittest.TestCase):
    def test_uno_de_afuera_no_llega_a_mandar(self):
        with _Falso() as g:
            r = s.mandar_correo(["socio@empresa.test", "otro@afuera.test"], "Asunto", "Hola")
        self.assertIn("no está en la lista", r)
        self.assertEqual(g.mandados, [])

    def test_afuera_en_copia_tampoco(self):
        with _Falso() as g:
            s.mandar_correo(["socio@empresa.test"], "Asunto", "Hola", copia=["Socio <otro@afuera.test>"])
        self.assertEqual(g.mandados, [])

    def test_manda_a_la_direccion_normalizada_con_pie(self):
        with _Falso() as g:
            r = s.mandar_correo([" Yo@Empresa.test "], "Prueba", "Hola", copia=["colega@empresa.test"])
        self.assertIn("Mandado desde yo@empresa.test", r)
        (m,) = g.mandados
        self.assertEqual((m["To"], m["Cc"], m["Bcc"]), ("yo@empresa.test", "colega@empresa.test", None))
        self.assertIn("Lo mandó Claude", m.get_body().get_content())

    def test_adjunto_no_permitido_no_manda(self):
        with _Falso() as g:
            r = s.mandar_correo(["yo@empresa.test"], "a", "b", adjuntos=[_pdf("secreto.env")])
        self.assertIn("solo", r)
        self.assertEqual(g.mandados, [])

    def test_adjunto_va(self):
        with _Falso() as g:
            s.mandar_correo(["yo@empresa.test"], "a", "b", adjuntos=[_pdf()])
        self.assertEqual([a.get_filename() for a in g.mandados[0].iter_attachments()], ["informe.pdf"])

    def test_personal_solo_texto(self):
        with _Falso() as g:
            r = s.mandar_correo(["yo.personal@personal.test"], "a", "b", adjuntos=[_pdf()])
            self.assertIn("sin adjuntos", r)
            self.assertEqual(g.mandados, [])
            s.mandar_correo(["yo.personal@personal.test"], "a", "b")
        self.assertEqual(len(g.mandados), 1)

    def test_link_no_sale(self):
        with _Falso() as g:
            r = s.mandar_correo(["yo@empresa.test"], "a", "Entrá a https://evil.example")
        self.assertIn("links", r)
        self.assertEqual(g.mandados, [])

    def test_el_sexto_se_frena(self):
        with _Falso() as g:
            for _ in range(s.TOPE_ENVIOS + 1):
                r = s.mandar_correo(["yo@empresa.test"], "a", "b")
        self.assertIn("frené", r)
        self.assertEqual(len(g.mandados), s.TOPE_ENVIOS)

    def test_en_paralelo_tampoco_pasa_el_tope(self):
        with _Falso(demora=0.2) as g:
            hilos = [threading.Thread(target=s.mandar_correo, args=(["yo@empresa.test"], "a", "b"))
                     for _ in range(12)]
            for h in hilos:
                h.start()
            for h in hilos:
                h.join()
        self.assertEqual(len(g.mandados), s.TOPE_ENVIOS)

    def test_registra_mandados_y_rechazados(self):
        antes = len(_registro())
        with _Falso():
            s.mandar_correo(["yo@empresa.test"], "Uno", "b")
            s.mandar_correo(["otro@afuera.test"], "Dos", "b")
        nuevas = _registro()[antes:]
        self.assertEqual(len(nuevas), 2)
        self.assertIn('"mandado"', nuevas[0])
        self.assertIn('"rechazado"', nuevas[1])

    def test_si_el_registro_falla_igual_dice_que_salio(self):
        with _Falso() as g, mock.patch.object(s.boveda, "carpeta", side_effect=OSError("disco lleno")):
            r = s.mandar_correo(["yo@empresa.test"], "a", "b")
        self.assertIn("Mandado", r)
        self.assertIn("no pude anotarlo", r)
        self.assertEqual(len(g.mandados), 1)


class Adjuntos(unittest.TestCase):
    def test_tipos_no_permitidos(self):
        for nombre in (".env", "llave.dpapi", "datos.json", "x.exe", "sin_extension", "correo.eml"):
            with self.assertRaises(s._Rechazado, msg=nombre):
                s.validar_adjuntos([_pdf(nombre)])

    def test_rutas_de_red_y_relativas(self):
        # `.invalid` nunca resuelve: si el chequeo se rompe, Windows no sale a buscar el host a la red.
        for ruta in (r"\\nadie.invalid\share\x.pdf", r"\\?\C:\x.pdf", r"\\.\C:\x.pdf", "//nadie.invalid/x.pdf",
                     "informe.pdf"):
            with self.assertRaises(s._Rechazado, msg=ruta):
                s.validar_adjuntos([ruta])

    def test_bajado_de_un_correo(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(s, "CARPETA_ADJUNTOS", Path(d)):
            p = Path(d) / "factura.pdf"
            p.write_bytes(b"x")
            with self.assertRaises(s._Rechazado):
                s.validar_adjuntos([str(p)])

    def test_vinculo_permanente(self):
        secreto = Path(_pdf("secreto.env"))
        disfraz = secreto.with_name("informe.pdf")
        os.link(secreto, disfraz)
        with self.assertRaises(s._Rechazado):
            s.validar_adjuntos([str(disfraz)])

    def test_tope_de_tamano(self):
        with mock.patch.object(s, "TOPE_ADJUNTOS", 15), self.assertRaises(s._Rechazado):
            s.validar_adjuntos([_pdf("a.pdf"), _pdf("b.pdf")])


class Lista(unittest.TestCase):
    def test_lee_direcciones_y_marca(self):
        self.assertEqual(s.LISTA_BLANCA, {"socio@empresa.test", "colega@empresa.test", "yo@empresa.test",
                                          "yo.personal@personal.test"})
        self.assertEqual(s.SOLO_SIN_ADJUNTOS, {"yo.personal@personal.test"})

    def test_sin_archivo_no_sale_nada(self):
        self.assertEqual(s.cargar_lista(Path(tempfile.mkdtemp()) / "no.txt"), (frozenset(), frozenset()))
        with mock.patch.object(s, "LISTA_BLANCA", frozenset()), _Falso() as g:
            r = s.mandar_correo(["yo@empresa.test"], "a", "b")
        self.assertIn("No hay destinatarios permitidos", r)
        self.assertEqual(g.mandados, [])

    def test_el_repo_no_trae_las_direcciones_de_la_lista_local(self):
        reales, _ = s.cargar_lista(s.ARCHIVO_LISTA)   # el archivo verdadero, fuera de git
        if not reales:
            self.skipTest("no hay lista-blanca.txt en esta máquina")
        carpeta = Path(s.__file__).parent
        for archivo in [*carpeta.glob("*.py"), *carpeta.glob("*.md")]:
            texto = archivo.read_text(encoding="utf-8").lower()
            for d in reales:
                self.assertNotIn(d, texto, f"{d} aparece en {archivo.name}, que va al repo público")


class Mensaje(unittest.TestCase):
    def test_renglon_largo_no_se_parte_al_leerlo(self):
        largo = "palabra " * 40
        m = s.armar_mensaje("a@b", ["yo@empresa.test"], [], "Asunto", largo, [])
        leido = email.message_from_bytes(m.as_bytes(), policy=policy.default).get_body().get_content()
        self.assertIn(largo.rstrip(), leido)


    def test_asunto_con_salto_de_linea(self):
        with self.assertRaises(s._Rechazado):
            s.armar_mensaje("a@b", ["yo@empresa.test"], [], "Hola\nBcc: otro@afuera.test", "x", [])

    def test_sin_texto(self):
        with self.assertRaises(s._Rechazado):
            s.armar_mensaje("a@b", ["yo@empresa.test"], [], "Asunto", "  ", [])


if __name__ == "__main__":
    unittest.main()
