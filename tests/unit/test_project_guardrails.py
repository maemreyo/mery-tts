from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PACKAGE_FILES = [
    "src/mery_tts/diagnostics/__init__.py",
    "src/mery_tts/diagnostics/doctor.py",
    "src/mery_tts/models/__init__.py",
    "src/mery_tts/models/events.py",
    "src/mery_tts/models/store.py",
    "src/mery_tts/catalog/fixtures/bundled-v1.json",
    "src/mery_tts/py.typed",
]


def test_pytest_declares_test_layer_markers() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()

    assert '"unit: fast tests for isolated package units"' in pyproject
    assert '"contract: API and schema contract tests using local fakes"' in pyproject
    assert '"cli: command-line interface tests that avoid real engine downloads"' in pyproject
    assert '"engine: tests that require a real engine binary/package installed' in pyproject
    assert (
        '"integration: tests that start a real server or may trigger model downloads"' in pyproject
    )


def test_test_suite_uses_unit_contract_and_cli_directories() -> None:
    assert (ROOT / "tests" / "unit").is_dir()
    assert (ROOT / "tests" / "contract").is_dir()
    assert (ROOT / "tests" / "cli").is_dir()


def test_make_test_excludes_engine_and_integration_markers() -> None:
    makefile = (ROOT / "Makefile").read_text()

    assert 'uv run pytest -m "not engine and not integration"' in makefile


def test_ci_separates_core_and_real_runtime_marker_jobs() -> None:
    workflow = (ROOT / ".github" / "workflows" / "check.yml").read_text()

    assert "- run: make check" in workflow
    assert "run_real_runtime" in workflow
    assert "uv sync --extra dev --extra all" in workflow
    assert 'uv run pytest -m "engine or integration"' in workflow
    assert "if: github.event_name == 'workflow_dispatch'" in workflow


def test_ci_exposes_optional_engine_extra_smoke_matrix() -> None:
    workflow = (ROOT / ".github" / "workflows" / "check.yml").read_text()

    assert "run_extra_smoke" in workflow
    assert "optional-engine-extra-smoke" in workflow
    assert "extra: [piper-plus, kokoro, all]" in workflow
    assert "uv sync --extra dev --extra ${{ matrix.extra }}" in workflow
    assert "uv run mery --help >/dev/null" in workflow
    assert "uv run mery --version >/dev/null" in workflow
    assert "uv run mery engines >/dev/null" in workflow


def test_ruff_and_strict_mypy_guardrails_are_configured() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()
    makefile = (ROOT / "Makefile").read_text()

    assert "[tool.ruff]" in pyproject
    assert 'src            = ["src"]' in pyproject
    assert "strict             = true" in pyproject
    assert 'files              = ["src/mery_tts"]' in pyproject
    assert "uv run ruff format --check src tests" in makefile
    assert "uv run ruff check src tests" in makefile
    assert "uv run mypy src/mery_tts" in makefile


def test_packaging_metadata_declares_typed_src_package() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()

    assert 'requires-python = ">=3.12"' in pyproject
    assert 'build-backend = "hatchling.build"' in pyproject
    assert 'packages = ["src/mery_tts"]' in pyproject
    assert (ROOT / "src" / "mery_tts" / "py.typed").is_file()


def test_package_install_smoke_harness_is_documented() -> None:
    makefile = (ROOT / "Makefile").read_text()
    report = (ROOT / "docs" / "reports" / "package-install-appliance-smoke.md").read_text()

    package_smoke_command = (
        "uv run python tools/package_smoke/run.py "
        "--repo-root . --artifact-dir .scratch/package-smoke"
    )

    assert "package-smoke:" in makefile
    assert package_smoke_command in makefile
    assert "make package-smoke" in report
    assert "tools/package_smoke/run.py" in report
    assert "package-smoke-result.json" in report


def test_packaging_runtime_files_are_not_hidden_by_ignore_rules() -> None:
    gitignore = (ROOT / ".gitignore").read_text()
    pyproject = (ROOT / "pyproject.toml").read_text()

    assert "/models/" in gitignore
    assert "/diagnostics/" in gitignore
    assert "models/" not in gitignore.replace("/models/", "")
    assert "diagnostics/" not in gitignore.replace("/diagnostics/", "")
    for file_path in RUNTIME_PACKAGE_FILES:
        assert (ROOT / file_path).is_file()
    assert "[tool.hatch.build.targets.sdist]" in pyproject
    assert '"/.scratch"' in pyproject
    assert '"/models"' in pyproject
    assert '"/diagnostics"' in pyproject


def test_adr_0048_p1_release_gate_is_documented() -> None:
    report = (ROOT / "docs" / "reports" / "adr-0048-p1-release-gate.md").read_text()
    readme = (ROOT / "README.md").read_text()
    docs_index = (ROOT / "docs" / "README.md").read_text()

    required_phrases = [
        "make check",
        "make package-smoke",
        "make piper-real-voice-smoke",
        "mery launch",
        "support bundle",
        "stable-additive",
        "CPU is the P1 baseline",
        "review-pass-needed",
        "Native signed installer",
        "One-click factory reset",
    ]
    for phrase in required_phrases:
        assert phrase in report
    assert "adr-0048-p1-release-gate.md" in docs_index
    assert "uv tool" in readme
    assert "pipx" in readme
    assert "one package release channel" in readme
    assert "Language support is model-dependent" in readme


def test_engine_dependencies_are_optional_extras_not_default_dependencies() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()
    default_dependencies = pyproject.split("[project.optional-dependencies]", maxsplit=1)[0]

    assert 'piper-plus = ["piper-plus>=1.10.0"]' in pyproject
    assert 'kokoro     = ["kokoro-onnx>=0.4", "onnxruntime>=1.16"]' in pyproject
    assert 'all        = ["mery-tts-server[piper-plus,kokoro]"]' in pyproject
    assert "piper-plus" not in default_dependencies
    assert "kokoro-onnx" not in default_dependencies
