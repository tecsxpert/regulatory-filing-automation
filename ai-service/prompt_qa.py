from __future__ import annotations

import argparse
import string
from pathlib import Path


PROMPT_EXPECTATIONS = {
    "categorise.txt": {
        "required_variables": {"text"},
        "required_terms": {"json", "category", "confidence", "reasoning"},
    },
    "generate_report.txt": {
        "required_variables": {"company", "filing_type", "period", "notes"},
        "required_terms": {"todo", "structured", "draft"},
    },
}


def _template_variables(template: str) -> set[str]:
    variables: set[str] = set()
    for _, field_name, _, _ in string.Formatter().parse(template):
        if field_name:
            variables.add(field_name.split(".", 1)[0].split("[", 1)[0])
    return variables


def check_prompt(path: Path) -> list[str]:
    expected = PROMPT_EXPECTATIONS.get(path.name)
    if expected is None:
        return []

    text = path.read_text(encoding="utf-8")
    lower_text = text.lower()
    failures: list[str] = []

    variables = _template_variables(text)
    missing_variables = expected["required_variables"] - variables
    if missing_variables:
        failures.append(
            f"{path.name}: missing template variables {sorted(missing_variables)}"
        )

    missing_terms = {
        term for term in expected["required_terms"] if term not in lower_text
    }
    if missing_terms:
        failures.append(f"{path.name}: missing guidance terms {sorted(missing_terms)}")

    try:
        text.format(**{name: f"<{name}>" for name in variables})
    except Exception as exc:
        failures.append(f"{path.name}: format failed: {exc}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AI prompt templates.")
    parser.add_argument(
        "--prompts-dir",
        default=Path(__file__).with_name("prompts"),
        type=Path,
    )
    args = parser.parse_args()

    failures: list[str] = []
    for prompt_name in sorted(PROMPT_EXPECTATIONS):
        failures.extend(check_prompt(args.prompts_dir / prompt_name))

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("Prompt QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
