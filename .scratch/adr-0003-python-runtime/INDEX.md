# ADR-0003 — Python-first runtime

Source ADR: `docs/adr/ADR-0003-python-runtime.md`

## Goal

Set up Python 3.12+ as a strict, typed, product-grade runtime using `uv`, hatchling, `ruff`, `mypy --strict`, optional engine extras, and a `src/` package layout.

## Issues

1. [Configure typed Python packaging with uv and hatchling](issues/01-configure-typed-python-packaging-with-uv-and-hatchling.md)
2. [Add lint typecheck and test guardrails](issues/02-add-lint-typecheck-and-test-guardrails.md)
3. [Isolate engine dependencies as optional extras](issues/03-isolate-engine-dependencies-as-optional-extras.md)
