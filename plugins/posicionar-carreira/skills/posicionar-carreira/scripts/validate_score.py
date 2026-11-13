#!/usr/bin/env python3
"""Valida e recalcula deterministicamente o score de uma oportunidade."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


WEIGHTS = {
    "alinhamento_funcao": Decimal("0.30"),
    "senioridade_autonomia": Decimal("0.20"),
    "segmento_contexto": Decimal("0.15"),
    "modalidade_localizacao": Decimal("0.15"),
    "competencias_evidencias": Decimal("0.10"),
    "remuneracao_contrato": Decimal("0.10"),
}


class ValidationError(ValueError):
    pass


def _decimal_score(value: object, name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{name}.score deve ser numerico")
    score = Decimal(str(value))
    if score < 0 or score > 10:
        raise ValidationError(f"{name}.score deve estar entre 0 e 10")
    return score


def _round(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def validate(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValidationError("a entrada deve ser um objeto JSON")

    sufficient = payload.get("sufficient_information")
    if not isinstance(sufficient, bool):
        raise ValidationError("sufficient_information deve ser booleano")

    if not sufficient:
        missing = payload.get("missing_information", [])
        if not isinstance(missing, list) or not all(
            isinstance(item, str) and item.strip() for item in missing
        ):
            raise ValidationError("missing_information deve ser uma lista de textos")
        return {
            "status": "informacao_insuficiente",
            "missing_information": missing,
            "weighted_score": None,
            "final_score": None,
            "label": None,
            "disqualified": False,
            "disqualifier_reason": None,
        }

    dimensions = payload.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ValidationError("dimensions deve ser um objeto")

    missing_dimensions = [name for name in WEIGHTS if name not in dimensions]
    if missing_dimensions:
        raise ValidationError(
            "dimensoes ausentes: " + ", ".join(missing_dimensions)
        )

    validated_dimensions = {}
    scores = {}
    for name in WEIGHTS:
        dimension = dimensions[name]
        if not isinstance(dimension, dict):
            raise ValidationError(f"{name} deve conter score e justification")
        score = _decimal_score(dimension.get("score"), name)
        justification = dimension.get("justification")
        if not isinstance(justification, str) or not justification.strip():
            raise ValidationError(f"{name}.justification deve ser texto nao vazio")
        scores[name] = score
        validated_dimensions[name] = {
            "score": float(score),
            "justification": justification.strip(),
        }

    disqualifier = payload.get("disqualifier")
    if not isinstance(disqualifier, dict):
        raise ValidationError("disqualifier deve ser um objeto")
    confirmed = disqualifier.get("confirmed")
    if not isinstance(confirmed, bool):
        raise ValidationError("disqualifier.confirmed deve ser booleano")
    reason = disqualifier.get("reason")
    if confirmed and (not isinstance(reason, str) or not reason.strip()):
        raise ValidationError("desqualificador confirmado exige reason")
    if not confirmed:
        reason = None

    weighted = sum(scores[name] * weight for name, weight in WEIGHTS.items())
    weighted = _round(weighted)
    role_alignment = scores["alinhamento_funcao"]

    if confirmed:
        final = Decimal("0.0")
        label = "Disqualified"
    else:
        if role_alignment <= 4:
            final = min(weighted, Decimal("4.0"))
        elif role_alignment <= 6:
            final = min(weighted, Decimal("6.5"))
        else:
            final = weighted
        final = _round(final)

        if final >= Decimal("8.5") and role_alignment >= 8:
            label = "Strong fit"
        elif final >= Decimal("7.0") and role_alignment >= 6:
            label = "Moderate fit"
        elif final >= Decimal("5.0"):
            label = "Weak fit"
        else:
            label = "Poor fit"

    return {
        "status": "scored",
        "dimensions": validated_dimensions,
        "weighted_score": float(weighted),
        "final_score": float(final),
        "label": label,
        "disqualified": confirmed,
        "disqualifier_reason": reason.strip() if confirmed else None,
    }


def _load(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"arquivo nao encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"JSON invalido: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida notas por dimensao e recalcula o score final."
    )
    parser.add_argument("input", type=Path, help="arquivo JSON de entrada (relativo ao diretório atual ou absoluto)")
    parser.add_argument("--output", type=Path, help="arquivo novo para o resultado (relativo ao diretório atual ou absoluto)")
    args = parser.parse_args()

    try:
        result = validate(_load(args.input))
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            if args.output.exists():
                raise ValidationError(f"arquivo de saida ja existe: {args.output}")
            args.output.write_text(rendered, encoding="utf-8", newline="")
        else:
            sys.stdout.write(rendered)
        return 0
    except (OSError, ValidationError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
