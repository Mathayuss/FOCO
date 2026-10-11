import hashlib
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]
SCRIPT = RAIZ / "infraestrutura" / "scripts" / "preparar_release.sh"


class PacoteReleaseTests(unittest.TestCase):
    def test_pacote_usa_configuracao_de_producao_sem_segredos(self):
        with tempfile.TemporaryDirectory() as temporario:
            destino = Path(temporario)
            subprocess.run(
                ["bash", str(SCRIPT), "0.0.0-teste", str(destino)],
                cwd=RAIZ,
                check=True,
            )

            pacote = destino / "FOCO-v0.0.0-teste.tar.gz"
            checksum = destino / "FOCO-v0.0.0-teste.tar.gz.sha256"
            self.assertTrue(pacote.is_file())
            self.assertTrue(checksum.is_file())
            self.assertEqual(
                checksum.read_text(encoding="utf-8").split()[0],
                hashlib.sha256(pacote.read_bytes()).hexdigest(),
            )

            with tarfile.open(pacote, "r:gz") as arquivo:
                nomes = {item.name.removeprefix("./") for item in arquivo.getmembers()}
                self.assertNotIn(".env", nomes)
                self.assertIn(".env.example", nomes)

                def texto(nome: str) -> str:
                    membro = arquivo.getmember(f"./{nome}")
                    conteudo = arquivo.extractfile(membro)
                    assert conteudo is not None
                    return conteudo.read().decode("utf-8")

                self.assertEqual(texto("VERSAO").strip(), "0.0.0-teste")
                compose = texto("docker-compose.yml")
                self.assertIn('${FOCO_PORTA_HTTP:-8080}:80', compose)
                self.assertNotIn('127.0.0.1:5432:5432', compose)
                self.assertIn('VITE_LIMITE_IMPORTACAO_MB:-512', compose)
                self.assertIn("AS construtor", texto("frontend/Dockerfile"))
                self.assertIn("client_max_body_size 512m", texto("frontend/nginx.conf"))
                exemplo = texto(".env.example")
                self.assertIn("VERSAO_FOCO=0.0.0-teste", exemplo)
                self.assertIn("VITE_API_URL=/api/v1", exemplo)
                self.assertIn("LIMITE_IMPORTACAO_MB=512", exemplo)


if __name__ == "__main__":
    unittest.main()
