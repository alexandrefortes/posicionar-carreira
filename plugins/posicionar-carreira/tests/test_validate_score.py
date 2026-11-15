import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/posicionar-carreira/scripts/validate_score.py"
SPEC = importlib.util.spec_from_file_location("validate_score", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def payload(role=9, other=8, compensation=5):
    values = {
        "alinhamento_funcao": role,
        "senioridade_autonomia": other,
        "segmento_contexto": other,
        "modalidade_localizacao": other,
        "competencias_evidencias": other,
        "remuneracao_contrato": compensation,
    }
    return {
        "sufficient_information": True,
        "dimensions": {
            name: {"score": score, "justification": f"Evidencia para {name}."}
            for name, score in values.items()
        },
        "disqualifier": {"confirmed": False, "reason": None},
    }


class ValidateScoreTests(unittest.TestCase):
    def test_strong_fit_for_compatible_executive_role_with_neutral_salary(self):
        result = MODULE.validate(payload(role=9, other=9))
        self.assertEqual(result["final_score"], 8.6)
        self.assertEqual(result["label"], "Strong fit")

    def test_confirmed_missing_mandatory_specialty_disqualifies(self):
        data = payload()
        data["disqualifier"] = {"confirmed": True, "reason": "Usuario confirmou nao possuir a especialidade obrigatoria."}
        result = MODULE.validate(data)
        self.assertEqual(result["final_score"], 0.0)
        self.assertEqual(result["label"], "Disqualified")

    def test_junior_role_is_capped_as_poor_fit(self):
        result = MODULE.validate(payload(role=3, other=10, compensation=10))
        self.assertEqual(result["final_score"], 4.0)
        self.assertEqual(result["label"], "Poor fit")

    def test_mandatory_language_can_disqualify(self):
        data = payload()
        data["disqualifier"] = {"confirmed": True, "reason": "Idioma obrigatorio nao dominado."}
        self.assertTrue(MODULE.validate(data)["disqualified"])

    def test_confirmed_incompatible_contract_can_disqualify(self):
        data = payload()
        data["disqualifier"] = {"confirmed": True, "reason": "Vinculo contratual obrigatorio que o usuario confirmou nao aceitar."}
        self.assertEqual(MODULE.validate(data)["label"], "Disqualified")

    def test_insufficient_description_has_no_score(self):
        result = MODULE.validate({
            "sufficient_information": False,
            "missing_information": ["responsabilidades", "requisitos"],
        })
        self.assertEqual(result["status"], "informacao_insuficiente")
        self.assertIsNone(result["final_score"])
        self.assertIsNone(result["label"])

    def test_low_role_alignment_caps_high_secondary_scores(self):
        result = MODULE.validate(payload(role=6, other=10, compensation=10))
        self.assertEqual(result["weighted_score"], 8.8)
        self.assertEqual(result["final_score"], 6.5)
        self.assertEqual(result["label"], "Weak fit")

    def test_model_overall_score_is_ignored(self):
        data = payload(role=3, other=3, compensation=3)
        data["overall_score"] = 10
        result = MODULE.validate(data)
        self.assertEqual(result["final_score"], 3.0)

    def test_missing_dimension_fails(self):
        data = payload()
        del data["dimensions"]["segmento_contexto"]
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate(data)

    def test_out_of_range_score_fails(self):
        data = payload()
        data["dimensions"]["alinhamento_funcao"]["score"] = 11
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate(data)

    def test_empty_justification_fails(self):
        data = payload()
        data["dimensions"]["alinhamento_funcao"]["justification"] = ""
        with self.assertRaises(MODULE.ValidationError):
            MODULE.validate(data)

    def test_cli_refuses_to_overwrite_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "input.json"
            output_path = root / "result.json"
            input_path.write_text(json.dumps(payload()), encoding="utf-8")
            output_path.write_text("existing", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(input_path), "--output", str(output_path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "existing")

    def test_cli_resolves_relative_paths_in_current_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            trabalho = Path(temp_dir)
            carreira = trabalho / "dados-exemplo"
            (carreira / "oportunidades").mkdir(parents=True)
            (trabalho / "entrada.json").write_text(json.dumps(payload()), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "entrada.json", "--output", "resultado.json"],
                cwd=trabalho, env={**os.environ, "CARREIRA_ROOT": str(carreira)},
                capture_output=True, encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((trabalho / "resultado.json").read_text(encoding="utf-8")),
                             MODULE.validate(payload()))
            self.assertFalse((carreira / "resultado.json").exists())


if __name__ == "__main__":
    unittest.main()
