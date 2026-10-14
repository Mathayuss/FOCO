import importlib.util
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verificar_bi_operacional.py"
SPEC = importlib.util.spec_from_file_location("verificar_bi_operacional", SCRIPT)
smoke = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(smoke)


class ComparacaoAnualTests(TestCase):
    def setUp(self):
        self.filtros = {
            "periods": [
                {"key": "2025-01"},
                {"key": "2025-02"},
                {"key": "2026-01"},
                {"key": "2026-02"},
                {"key": "2026-03"},
                {"key": "ano-2025"},
                {"key": "ano-2026"},
            ]
        }
        self.painel = {
            "overview": {
                "comparison": {
                    "available": True,
                    "current_label": "Jan-Fev/2026",
                    "baseline_label": "Jan-Fev/2025",
                    "current_total": 30,
                    "baseline_total": 24,
                    "reason": "Comparacao limitada aos meses equivalentes.",
                }
            },
            "monthly": {
                "items": [
                    {"mes": "Jan/2026"},
                    {"mes": "Fev/2026"},
                    {"mes": "Mar/2026"},
                ],
                "comparison": [
                    {"current_month": "Jan/2026", "baseline_month": "Jan/2025", "current": 10, "baseline": 8},
                    {"current_month": "Fev/2026", "baseline_month": "Fev/2025", "current": 20, "baseline": 16},
                ],
            },
        }

    def test_valida_meses_equivalentes_e_cobertura_parcial(self):
        with patch.object(smoke, "_get", return_value=self.painel):
            resultado = smoke._verificar_comparacao_anual("http://localhost/api/v1", self.filtros, 1)

        self.assertEqual(resultado, "Jan-Fev/2026 vs Jan-Fev/2025")

    def test_rejeita_pareamento_com_mes_diferente(self):
        self.painel["monthly"]["comparison"][1]["baseline_month"] = "Mar/2025"
        with patch.object(smoke, "_get", return_value=self.painel):
            with self.assertRaisesRegex(smoke.ErroSmoke, "meses que nao sao equivalentes"):
                smoke._verificar_comparacao_anual("http://localhost/api/v1", self.filtros, 1)

    def test_rejeita_soma_anual_inconsistente(self):
        self.painel["overview"]["comparison"]["current_total"] = 31
        with patch.object(smoke, "_get", return_value=self.painel):
            with self.assertRaisesRegex(smoke.ErroSmoke, "divergem da soma"):
                smoke._verificar_comparacao_anual("http://localhost/api/v1", self.filtros, 1)


if __name__ == "__main__":
    import unittest

    unittest.main()
