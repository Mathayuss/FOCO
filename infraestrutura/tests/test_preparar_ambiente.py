import importlib.util
from io import StringIO
import os
from pathlib import Path
import stat
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "preparar_ambiente.py"
SPEC = importlib.util.spec_from_file_location("preparar_ambiente", SCRIPT)
preparador = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(preparador)

SEGREDO_TESTE = "a" * 64


def escrever_modelo(caminho: Path) -> None:
    caminho.write_text(
        """VERSAO_FOCO=0.3.1
AMBIENTE=producao
BD_USUARIO=foco
BD_SENHA=troque-esta-senha-antes-de-iniciar
BD_NOME=foco_ocorrencias
DATABASE_URL=postgresql+psycopg://foco:troque-esta-senha-antes-de-iniciar@bd:5432/foco_ocorrencias
LIMITE_IMPORTACAO_MB=512
""",
        encoding="utf-8",
    )


class PrepararAmbienteTests(unittest.TestCase):
    def executar(self, modelo: Path, destino: Path):
        stdout = StringIO()
        stderr = StringIO()
        with (
            patch.object(preparador.secrets, "token_hex", return_value=SEGREDO_TESTE),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            codigo = preparador.main(["--modelo", str(modelo), "--arquivo", str(destino)])
        self.assertNotIn(SEGREDO_TESTE, stdout.getvalue())
        self.assertNotIn(SEGREDO_TESTE, stderr.getvalue())
        return codigo, stdout.getvalue(), stderr.getvalue()

    def test_cria_ambiente_atomico_com_permissao_restrita(self):
        with tempfile.TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            modelo = raiz / ".env.example"
            destino = raiz / ".env"
            escrever_modelo(modelo)

            codigo, stdout, stderr = self.executar(modelo, destino)

            self.assertEqual(codigo, 0)
            self.assertEqual(stderr, "")
            self.assertIn("criado", stdout.casefold())
            conteudo = destino.read_text(encoding="utf-8")
            self.assertIn(f"BD_SENHA={SEGREDO_TESTE}", conteudo)
            self.assertIn(
                f"DATABASE_URL=postgresql+psycopg://foco:{SEGREDO_TESTE}@bd:5432/foco_ocorrencias",
                conteudo,
            )
            self.assertEqual(stat.S_IMODE(destino.stat().st_mode), 0o600)
            self.assertEqual(modelo.read_text(encoding="utf-8").count(SEGREDO_TESTE), 0)
            self.assertEqual(list(raiz.glob(".env.*.tmp")), [])

    def test_preserva_ambiente_existente_valido_e_corrige_permissao(self):
        with tempfile.TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            modelo = raiz / ".env.example"
            destino = raiz / ".env"
            escrever_modelo(modelo)
            original = (
                "BD_USUARIO=foco\n"
                "BD_SENHA=segredo-ja-configurado\n"
                "BD_NOME=foco_ocorrencias\n"
                "DATABASE_URL=postgresql+psycopg://foco:segredo-ja-configurado@bd:5432/foco_ocorrencias\n"
            )
            destino.write_text(original, encoding="utf-8")
            os.chmod(destino, 0o644)

            codigo, stdout, stderr = self.executar(modelo, destino)

            self.assertEqual(codigo, 0)
            self.assertEqual(stderr, "")
            self.assertIn("preservado", stdout.casefold())
            self.assertEqual(destino.read_text(encoding="utf-8"), original)
            self.assertEqual(stat.S_IMODE(destino.stat().st_mode), 0o600)

    def test_recusa_ambiente_existente_com_senha_padrao(self):
        with tempfile.TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            modelo = raiz / ".env.example"
            destino = raiz / ".env"
            escrever_modelo(modelo)
            original = modelo.read_text(encoding="utf-8")
            destino.write_text(original, encoding="utf-8")

            codigo, _, stderr = self.executar(modelo, destino)

            self.assertEqual(codigo, 1)
            self.assertIn("senha padrao", stderr.casefold())
            self.assertEqual(destino.read_text(encoding="utf-8"), original)

    def test_recusa_modelo_incompleto_sem_criar_arquivo(self):
        with tempfile.TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            modelo = raiz / ".env.example"
            destino = raiz / ".env"
            modelo.write_text("BD_USUARIO=foco\n", encoding="utf-8")

            codigo, _, stderr = self.executar(modelo, destino)

            self.assertEqual(codigo, 1)
            self.assertIn("incompleto", stderr.casefold())
            self.assertFalse(destino.exists())

    def test_recusa_destino_simbolico(self):
        with tempfile.TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            modelo = raiz / ".env.example"
            real = raiz / "real.env"
            destino = raiz / ".env"
            escrever_modelo(modelo)
            real.write_text("nao alterar\n", encoding="utf-8")
            destino.symlink_to(real)

            codigo, _, stderr = self.executar(modelo, destino)

            self.assertEqual(codigo, 1)
            self.assertIn("simbolico", stderr.casefold())
            self.assertEqual(real.read_text(encoding="utf-8"), "nao alterar\n")


if __name__ == "__main__":
    unittest.main()
