import importlib.util
from io import StringIO
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

CAMINHO = Path(__file__).resolve().parents[1] / "scripts" / "verificar_banco_docker.py"
SPEC = importlib.util.spec_from_file_location("verificar_banco_docker", CAMINHO)
verificador = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verificador)
MARCADOR = "SEGREDO_FICTICIO_APENAS_PARA_TESTES"


def configuracao(ip="127.0.0.1"):
    return {"services": {
        "bd": {
            "environment": {
                "POSTGRES_USER": "foco",
                "POSTGRES_PASSWORD": MARCADOR,
                "POSTGRES_DB": "foco_ocorrencias",
            },
            "ports": [{"host_ip": ip, "target": 5432, "published": "5432"}],
        },
        "servidor": {"environment": {
            "DATABASE_URL": f"postgresql+psycopg://foco:{MARCADOR}@bd:5432/foco_ocorrencias",
            "LIMITE_IMPORTACAO_MB": "512",
        }},
        "interface": {"environment": {"VITE_LIMITE_IMPORTACAO_MB": "512"}},
    }}


class TestConfiguracao(unittest.TestCase):
    def test_aceita_loopback_ipv4_e_ipv6(self):
        for ip in ["127.0.0.1", "::1"]:
            with self.subTest(ip=ip):
                self.assertEqual(verificador.validar_configuracao(configuracao(ip)), [])

    def test_recusa_ip_externo_ausente_ou_invalido(self):
        for ip in ["0.0.0.0", "::", "192.168.1.10", "100.90.0.1", "localhost", "", None, 7]:
            with self.subTest(ip=ip):
                self.assertTrue(verificador.validar_configuracao(configuracao(ip)))

    def test_aceita_banco_sem_publicacao_no_host(self):
        config = configuracao()
        config["services"]["bd"].pop("ports")
        self.assertEqual(verificador.validar_configuracao(config), [])

    def test_recusa_senha_ausente_ou_vazia(self):
        for senha in [None, "", " "]:
            with self.subTest(senha=senha):
                config = configuracao()
                config["services"]["bd"]["environment"]["POSTGRES_PASSWORD"] = senha
                self.assertTrue(verificador.validar_configuracao(config))

    def test_recusa_senhas_padrao(self):
        for senha in ["altere_esta_senha", "troque-esta-senha-antes-de-iniciar"]:
            with self.subTest(senha=senha):
                config = configuracao()
                config["services"]["bd"]["environment"]["POSTGRES_PASSWORD"] = senha
                config["services"]["servidor"]["environment"]["DATABASE_URL"] = (
                    f"postgresql+psycopg://foco:{senha}@bd:5432/foco_ocorrencias"
                )
                self.assertTrue(verificador.validar_configuracao(config))

    def test_recusa_database_url_ausente_invalida_ou_divergente(self):
        for url in [
            None,
            "",
            "invalida",
            "postgresql+psycopg://foco:outra@bd:5432/foco_ocorrencias",
            f"postgresql+psycopg://outro:{MARCADOR}@bd:5432/foco_ocorrencias",
            f"postgresql+psycopg://foco:{MARCADOR}@externo:5432/foco_ocorrencias",
            f"postgresql+psycopg://foco:{MARCADOR}@bd:5432/outro_banco",
        ]:
            with self.subTest(url=url):
                config = configuracao()
                config["services"]["servidor"]["environment"]["DATABASE_URL"] = url
                self.assertTrue(verificador.validar_configuracao(config))

    def test_recusa_servico_ausente_e_formatos_invalidos(self):
        for config in [{}, {"services": []}, {"services": {"bd": []}}]:
            with self.subTest(config=config):
                self.assertTrue(verificador.validar_configuracao(config))
        config = configuracao()
        for portas in [None, {}, ["5432:5432"]]:
            config["services"]["bd"]["ports"] = portas
            self.assertTrue(verificador.validar_configuracao(config))


class TestLimiteImportacao(unittest.TestCase):
    def test_aceita_limites_iguais_ate_512_mb(self):
        self.assertEqual(verificador.validar_limite_importacao(configuracao()), [])

    def test_aceita_limite_da_interface_como_argumento_de_build(self):
        config = configuracao()
        config["services"]["interface"].pop("environment")
        config["services"]["interface"]["build"] = {
            "args": {"VITE_LIMITE_IMPORTACAO_MB": "512"}
        }
        self.assertEqual(verificador.validar_limite_importacao(config), [])

    def test_recusa_limites_divergentes_dentro_da_interface(self):
        config = configuracao()
        config["services"]["interface"]["build"] = {
            "args": {"VITE_LIMITE_IMPORTACAO_MB": "256"}
        }
        self.assertTrue(verificador.validar_limite_importacao(config))

    def test_recusa_limite_ausente_invalido_ou_nao_positivo(self):
        for servico, variavel in (
            ("servidor", "LIMITE_IMPORTACAO_MB"),
            ("interface", "VITE_LIMITE_IMPORTACAO_MB"),
        ):
            for valor in [None, "", "invalido", 0, -1]:
                with self.subTest(servico=servico, valor=valor):
                    config = configuracao()
                    config["services"][servico]["environment"][variavel] = valor
                    self.assertTrue(verificador.validar_limite_importacao(config))

    def test_recusa_limites_divergentes(self):
        config = configuracao()
        config["services"]["interface"]["environment"]["VITE_LIMITE_IMPORTACAO_MB"] = "256"
        self.assertTrue(verificador.validar_limite_importacao(config))

    def test_recusa_limite_acima_do_maximo(self):
        config = configuracao()
        config["services"]["servidor"]["environment"]["LIMITE_IMPORTACAO_MB"] = "513"
        config["services"]["interface"]["environment"]["VITE_LIMITE_IMPORTACAO_MB"] = "513"
        self.assertTrue(verificador.validar_limite_importacao(config))


class TestPortasAtivas(unittest.TestCase):
    def test_aceita_loopback_ipv4_e_ipv6(self):
        portas = {"5432/tcp": [{"HostIp": "127.0.0.1"}, {"HostIp": "::1"}]}
        self.assertEqual(verificador.validar_portas_ativas(portas), [])

    def test_aceita_ausencia_de_publicacao(self):
        for portas in [{}, {"5432/tcp": None}, {"5432/tcp": []}]:
            self.assertEqual(verificador.validar_portas_ativas(portas), [])

    def test_recusa_um_unico_bind_externo_entre_binds_locais(self):
        for ip in ["0.0.0.0", "::", "10.0.0.1", "100.90.0.1", None]:
            portas = {"5432/tcp": [{"HostIp": "127.0.0.1"}, {"HostIp": ip}]}
            self.assertTrue(verificador.validar_portas_ativas(portas))

    def test_verifica_todas_as_portas_publicadas(self):
        portas = {"5432/tcp": [{"HostIp": "127.0.0.1"}], "5433/tcp": [{"HostIp": "0.0.0.0"}]}
        self.assertTrue(verificador.validar_portas_ativas(portas))

    def test_recusa_formatos_invalidos(self):
        for vinculos in [{}, "externo", [{}], [None]]:
            self.assertTrue(verificador.validar_portas_ativas({"5432/tcp": vinculos}))


class TestComandos(unittest.TestCase):
    def executar_cli(self, respostas, argumentos=None):
        saida = StringIO()
        with patch.object(verificador, "_executar", side_effect=respostas) as comando:
            with redirect_stdout(saida):
                codigo = verificador.main(argumentos or [])
        self.assertNotIn(MARCADOR, saida.getvalue())
        return codigo, json.loads(saida.getvalue()), comando

    def test_modo_configuracao_nao_consulta_containers(self):
        codigo, saida, comando = self.executar_cli([json.dumps(configuracao())])
        self.assertEqual(codigo, 0)
        self.assertEqual(saida["escopo"], "configuracao")
        comando.assert_called_once_with(["docker", "compose", "config", "--format", "json"])

    def test_detecta_configuracao_segura_com_container_ainda_exposto(self):
        codigo, saida, _ = self.executar_cli([
            json.dumps(configuracao()), "container-bd\n",
            json.dumps({"5432/tcp": [{"HostIp": "0.0.0.0", "HostPort": "5432"}]}),
        ], ["--verificar-execucao"])
        self.assertEqual(codigo, 1)
        self.assertEqual(saida["status"], "falha")
        self.assertIn("Container", saida["erros"][0])

    def test_confirma_configuracao_e_execucao_seguras(self):
        codigo, saida, comando = self.executar_cli([
            json.dumps(configuracao()), "container-bd\n",
            json.dumps({"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "5432"}]}),
        ], ["--verificar-execucao"])
        self.assertEqual(codigo, 0)
        self.assertEqual(saida["escopo"], "configuracao_e_execucao")
        self.assertEqual(comando.call_args.args[0], [
            "docker", "inspect", "--format", "{{json .NetworkSettings.Ports}}", "container-bd",
        ])

    def test_recusa_container_ausente_ou_ambiguo(self):
        for identificador in ["", "container-1\ncontainer-2\n"]:
            codigo, _, _ = self.executar_cli([
                json.dumps(configuracao()), identificador,
            ], ["--verificar-execucao"])
            self.assertEqual(codigo, 1)

    def test_recusa_json_invalido_sem_expor_conteudo(self):
        for resposta in [MARCADOR, json.dumps([MARCADOR]), "null"]:
            codigo, _, _ = self.executar_cli([resposta])
            self.assertEqual(codigo, 1)

    def test_recusa_formato_invalido_das_portas_ativas(self):
        codigo, _, _ = self.executar_cli([
            json.dumps(configuracao()), "container-bd", "null",
        ], ["--verificar-execucao"])
        self.assertEqual(codigo, 1)

    def test_falha_do_docker_nao_expoe_stdout_ou_stderr(self):
        erro = subprocess.CalledProcessError(1, ["docker"], output=MARCADOR, stderr=MARCADOR)
        with patch.object(verificador.subprocess, "run", side_effect=erro):
            with self.assertRaises(verificador.ErroVerificacao) as contexto:
                verificador._executar(["docker", "compose", "config", "--format", "json"])
        self.assertNotIn(MARCADOR, str(contexto.exception))

    def test_falta_do_docker_e_timeout_sao_erros_controlados(self):
        for erro in [FileNotFoundError(MARCADOR), subprocess.TimeoutExpired(["docker"], 30, output=MARCADOR)]:
            with patch.object(verificador.subprocess, "run", side_effect=erro):
                with self.assertRaises(verificador.ErroVerificacao) as contexto:
                    verificador._executar(["docker"])
            self.assertNotIn(MARCADOR, str(contexto.exception))


if __name__ == "__main__":
    unittest.main()
