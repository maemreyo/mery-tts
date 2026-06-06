.PHONY: check format-check lint typecheck typecheck-strict test smoke

check: format-check lint typecheck typecheck-strict test smoke

format-check:
	uv run ruff format --check src tests

lint:
	uv run ruff check src tests

typecheck:
	uv run mypy src/mery_tts

typecheck-strict:
	@output=$$(uv run basedpyright src/mery_tts 2>&1); \
	if echo "$$output" | grep -q " error:"; then \
		echo "$$output" | grep " error:"; \
		echo ""; \
		echo "basedpyright: errors found"; \
		exit 1; \
	fi
	@echo "basedpyright: 0 errors"

test:
	uv run pytest -m "not engine and not integration"

smoke:
	uv run mery --help >/dev/null
	uv run mery --version >/dev/null
	uv run mery engines >/dev/null
