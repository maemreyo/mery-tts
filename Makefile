.PHONY: check format-check lint typecheck test smoke

check: format-check lint typecheck test smoke

format-check:
	uv run ruff format --check src tests

lint:
	uv run ruff check src tests

typecheck:
	uv run mypy src/mery_tts

test:
	uv run pytest -m "not engine and not integration"

smoke:
	uv run mery --help >/dev/null
	uv run mery --version >/dev/null
	uv run mery engines >/dev/null
