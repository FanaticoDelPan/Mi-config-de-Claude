"""Tests de `boveda.py` y de los chequeos de `conectar.py` que no necesitan a Google.

    .venv\\Scripts\\python.exe -m unittest test_boveda -v
"""

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import boveda
import conectar


class TestBoveda(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.local = Path(self._tmp.name)
        self._env = mock.patch.dict(os.environ, {"LOCALAPPDATA": str(self.local)})
        self._env.start()
        self.paquete = self.local / "Packages" / "Claude_abc123" / "LocalCache" / "Local" / "mcp-mail-empresa"

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()

    def _guardar_en_paquete(self, contenido, tipo="lectura"):
        self.paquete.mkdir(parents=True, exist_ok=True)
        destino = self.paquete / boveda.ARCHIVOS[tipo]
        destino.write_bytes(boveda._cifrar(__import__("json").dumps(contenido).encode()))
        return destino

    def test_sin_pase(self):
        self.assertIsNone(boveda.ruta())
        self.assertIsNone(boveda.leer())
        self.assertIsNone(boveda.leer("envio"))

    def test_encuentra_el_de_la_copia_privada_de_la_app(self):
        self._guardar_en_paquete({"cuenta": "a@x"})
        self.assertEqual(boveda.leer(), {"cuenta": "a@x"})
        self.assertEqual(boveda.ruta().parent, self.paquete)

    def test_encuentra_el_del_lugar_real(self):
        destino = boveda.guardar({"cuenta": "real@x"})
        self.assertEqual(destino, self.local / "mcp-mail-empresa" / "llave.dpapi")
        self.assertEqual(boveda.leer(), {"cuenta": "real@x"})

    def test_con_los_dos_usa_el_mas_nuevo(self):
        viejo = self._guardar_en_paquete({"cuenta": "vieja"})
        os.utime(viejo, (time.time() - 3600, time.time() - 3600))
        boveda.guardar({"cuenta": "nueva"})
        self.assertEqual(boveda.leer()["cuenta"], "nueva")
        os.utime(viejo, (time.time() + 60, time.time() + 60))
        self.assertEqual(boveda.leer()["cuenta"], "vieja")

    def test_lectura_y_envio_no_se_cruzan(self):
        boveda.guardar({"cuenta": "lee"})
        self.assertIsNone(boveda.leer("envio"))
        self._guardar_en_paquete({"cuenta": "manda"}, "envio")
        self.assertEqual(boveda.leer("envio")["cuenta"], "manda")
        self.assertEqual(boveda.leer()["cuenta"], "lee")
        with self.assertRaises(ValueError):
            boveda.leer("todo")

    def test_conectar_reusa_el_cliente_de_cualquiera_de_los_pases(self):
        self._guardar_en_paquete({"cuenta": "a", "client_id": "ID", "client_secret": "S", "refresh_token": "R"})
        cliente = conectar._cliente_guardado("envio")
        self.assertEqual(cliente["installed"]["client_id"], "ID")
        self.assertNotIn("refresh_token", cliente["installed"])


class TestConectar(unittest.TestCase):
    def test_permisos_de_mas(self):
        self.assertEqual(conectar.permisos_de_mas("lectura", [conectar.LECTURA]), [])
        self.assertEqual(conectar.permisos_de_mas("lectura", f"{conectar.LECTURA} {conectar.ENVIO}"),
                         [conectar.ENVIO])
        self.assertEqual(conectar.permisos_de_mas("envio", [conectar.ENVIO, *conectar.IDENTIDAD]), [])
        self.assertEqual(conectar.permisos_de_mas("envio", [conectar.ENVIO, conectar.LECTURA]), [conectar.LECTURA])

    def test_mail_del_id_token(self):
        import base64
        import json

        def token(datos):
            cuerpo = base64.urlsafe_b64encode(json.dumps(datos).encode()).decode().rstrip("=")
            return f"x.{cuerpo}.y"
        self.assertEqual(conectar._mail_del_id_token(token({"email": "JSmith@X.com", "email_verified": True})),
                         "jsmith@x.com")
        self.assertIsNone(conectar._mail_del_id_token(token({"email": "a@x", "email_verified": False})))
        self.assertIsNone(conectar._mail_del_id_token(None))
        self.assertIsNone(conectar._mail_del_id_token("basura"))


if __name__ == "__main__":
    unittest.main()
