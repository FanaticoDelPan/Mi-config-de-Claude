"""Prueba de mutación del chequeo de gatillos: fabrica cada señal en un repo descartable y verifica que
TODAVÍA la caza, que un repo vacío no avisa nada, y que el chequeo y el documento hablan de las mismas filas.
Si esto falla, el chequeo puede estar en verde sin medir nada.

    python -I scripts/test_chequear_gatillos.py
"""

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # importar el chequeo no deja un __pycache__ en el repo del proyecto
_spec = importlib.util.spec_from_file_location("chequear_gatillos", AQUI / "chequear_gatillos.py")
cg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cg)

# La fecha se arma por partes: escrita entera, este mismo archivo dispararía el gatillo en el proyecto.
FECHA = "20" + "26-01-15"


class RepoDescartable(unittest.TestCase):
    def setUp(self):
        cg._todos.cache_clear()  # cada test cambia archivos: la lista no se reusa entre corridas
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self._tmp.name)
        filas = "\n".join(f"| **{n}** | gatillo | pieza |" for n in cg.GATILLOS)
        self.escribir("docs/escalar-el-arnes.md", f"| Pieza | Gatillo | Qué es |\n|---|---|---|\n{filas}\n")

    def tearDown(self):
        self._tmp.cleanup()

    def escribir(self, relativa, texto):
        ruta = self.raiz / relativa
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(texto, encoding="utf-8")

    def avisados(self):
        cg._todos.cache_clear()
        avisos, desajustes, errores, _ = cg.chequear(self.raiz)
        self.assertEqual(desajustes, [])
        self.assertEqual(errores, [])
        return {a.split(":")[0] for a in avisos}

    def test_repo_vacio_no_avisa_nada(self):
        self.assertEqual(self.avisados(), set())

    def test_cantidad_de_documentos(self):
        for i in range(9):  # con el de escalar-el-arnes, diez
            self.escribir(f"docs/doc{i}.md", "texto")
        self.assertEqual(self.avisados(), {"Prosa repetida", "Validador de enlaces internos"})

    def test_una_decision_declarada_silencia_solo_ese_gatillo(self):
        for i in range(9):
            self.escribir(f"docs/doc{i}.md", "texto")
        self.escribir("docs/gatillos.json", json.dumps({"Prosa repetida": "#7"}))
        self.assertEqual(self.avisados(), {"Validador de enlaces internos"})

    def test_declaracion_mal_escrita_frena(self):
        for valor in ("no", "no: corto", "hecho", 3):
            self.escribir("docs/gatillos.json", json.dumps({"Prosa repetida": valor}))
            self.assertTrue(cg.chequear(self.raiz)[2], f"aceptó el valor {valor!r}")

    def test_pendiente_vale_mientras_la_lista_lo_nombre(self):
        for i in range(9):
            self.escribir(f"docs/doc{i}.md", "texto")
        decl = {"Prosa repetida": "pendiente: docs/pendientes.md",
                "Validador de enlaces internos": "pendiente: docs/pendientes.md"}
        self.escribir("docs/gatillos.json", json.dumps(decl))
        self.escribir("docs/pendientes.md", "- Prosa repetida: falta el control\n")
        errores = cg.chequear(self.raiz)[2]
        self.assertEqual(len(errores), 1, errores)
        self.assertIn("Validador de enlaces internos", errores[0])

    def test_declarar_un_gatillo_que_no_existe_frena(self):
        self.escribir("docs/gatillos.json", json.dumps({"Gatillo viejo": "adoptada"}))
        self.assertTrue(cg.chequear(self.raiz)[2])

    def test_documento_que_perdio_una_fila_frena_solo_en_estricto(self):
        self.escribir("docs/escalar-el-arnes.md", "| **Prosa repetida** | x | y |\n")
        _, desajustes, errores, _ = cg.chequear(self.raiz)
        self.assertTrue(desajustes)
        self.assertEqual(errores, [])
        with contextlib.redirect_stdout(io.StringIO()):  # su salida esperada no se mezcla con la del test
            self.assertEqual(cg.main(["--raiz", str(self.raiz)]), 0)
            self.assertEqual(cg.main(["--raiz", str(self.raiz), "--estricto"]), 1)

    def test_fecha_en_comentario_si_en_texto_no(self):
        self.escribir("src/a.py", f'x = "{FECHA}"\n')
        self.assertEqual(self.avisados(), set())
        self.escribir("src/b.ts", f"// arreglado el {FECHA}\n")
        self.assertEqual(self.avisados(), {"Sin fechas ni autores en el código y los docs"})

    def test_carpetas_ajenas_no_cuentan(self):
        self.escribir("node_modules/x/a.js", f"// {FECHA}\n")
        self.escribir(".worktrees/otra/src/a.py", f"# {FECHA}\n")
        self.escribir(".claude/worktrees/otra/src/a.py", f"# {FECHA}\n")
        self.assertEqual(self.avisados(), set())

    def test_en_un_repo_lo_ignorado_por_git_no_cuenta(self):
        git = ["git", "-C", str(self.raiz)]
        subprocess.run(git + ["init", "-q"], check=True, env=cg.git_sin_herencia())
        self.escribir(".gitignore", "salida-del-build/\n")
        self.escribir("salida-del-build/chunk.js", f"// {FECHA}\n")
        self.assertEqual(self.avisados(), set())
        cg._todos.cache_clear()
        self.escribir("src/a.js", f"// {FECHA}\n")  # sin commitear todavía: igual es del proyecto
        self.assertEqual(self.avisados(), {"Sin fechas ni autores en el código y los docs"})

    def test_migracion_destructiva(self):
        self.escribir("alembic/versions/0003_x.py", "def upgrade():\n    op.add_column('t', c)\n")
        self.assertEqual(self.avisados(), set())
        self.escribir("alembic/versions/0004_y.py", "def upgrade():\n    op.drop_table('vieja')\n")
        self.assertEqual(self.avisados(), {"Piso de rollback"})

    def test_guia_de_area_y_skill_propio(self):
        self.escribir("docs/reglas-interfaz.md", "regla")
        self.escribir(".claude/skills/commitear/SKILL.md", "---\nname: commitear\n---\n")
        # la guía es además el segundo documento de docs/, así que también pide el validador de enlaces
        self.assertEqual(self.avisados(), {"Reglas que llegan solas", "Tope del cuerpo de cada skill",
                                           "Validador de enlaces internos"})

    def test_credenciales_propias_no_cuentan_y_ajenas_si(self):
        self.escribir(".env.example", "DATABASE_URL=\nREDIS_URL=\nSECRET_KEY=\nNEXT_PUBLIC_SUPABASE_URL=\n")
        self.assertEqual(self.avisados(), set())
        self.escribir(".env.example", "DATABASE_URL=\nERP_API_KEY=\n")
        self.assertEqual(self.avisados(), {"Método para conectar sistemas de otros"})

    def test_publicado_desde_la_maquina(self):
        publicado = {"Guarda de rama", "Revisor adversarial antes de publicar"}
        self.escribir("package.json", json.dumps({"name": "app", "private": True, "bin": {"x": "x.js"}}))
        self.assertEqual(self.avisados(), set())
        self.escribir("mcp/package.json", json.dumps({"name": "@alguien/x", "publishConfig": {"access": "public"}}))
        self.assertEqual(self.avisados(), publicado)
        (self.raiz / "mcp" / "package.json").unlink()
        self.escribir(".vercel/project.json", "{}")
        self.assertEqual(self.avisados(), publicado)

    def test_publicaciones_por_etiquetas(self):
        # Sin las GIT_* heredadas: corriendo adentro de un pre-commit, este git operaría sobre el repo real.
        git = ["git", "-C", str(self.raiz), "-c", "user.name=prueba", "-c", "user.email=prueba@ejemplo.com",
               "-c", "core.hooksPath=", "-c", "commit.gpgsign=false"]
        correr = lambda *a: subprocess.run(git + list(a), check=True, env=cg.git_sin_herencia())  # noqa: E731
        correr("init", "-q")
        correr("commit", "-q", "--allow-empty", "-m", "inicio")
        correr("tag", "v1")
        publicado = {"Guarda de rama", "Revisor adversarial antes de publicar"}
        self.assertEqual(self.avisados(), publicado)
        for n in range(2, 6):
            correr("tag", f"v{n}")
        self.assertEqual(self.avisados(), publicado | {"Registro de hallazgos por ángulo y de escapes a producción"})


class ConsistenciaConElDocumento(unittest.TestCase):
    def test_cada_gatillo_medido_es_una_fila_del_documento(self):
        doc = next((p for p in (AQUI / "escalar-el-arnes.md", AQUI.parent / "docs" / "escalar-el-arnes.md")
                    if p.is_file()), None)
        self.assertIsNotNone(doc, "no encuentro escalar-el-arnes.md al lado ni en docs/")
        filas = cg.filas_del_documento(doc.read_text(encoding="utf-8"))
        self.assertGreater(len(filas), 15, "el parser no encontró las filas: cambió el formato de la tabla")
        faltan = [n for n in cg.GATILLOS if n not in filas]
        self.assertEqual(faltan, [], "gatillos medidos que el documento ya no tiene")


if __name__ == "__main__":
    unittest.main(verbosity=1, argv=[sys.argv[0]])
