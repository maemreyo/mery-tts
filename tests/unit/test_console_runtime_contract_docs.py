from pathlib import Path

ROOT = Path(__file__).parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_core_runtime_contract_is_linked_and_covers_console_boundaries() -> None:
    contract = read("docs/architecture/core-runtime-contract.md")
    adr = read("docs/adr/ADR-0037-core-runtime-contract.md")
    docs_index = read("docs/README.md")
    agents = read("AGENTS.md")

    for phrase in [
        "Engine contract",
        "Voice contract",
        "Install/readiness contract",
        "Synthesis contract",
        "Streaming contract",
        "Error/diagnostic contract",
        "Storage contract",
        "Test contract",
        "generated client types",
        "fake-engine",
        "optional real-engine smoke",
        "out of scope",
    ]:
        assert phrase in contract

    assert "docs/architecture/core-runtime-contract.md" in agents
    assert "architecture/core-runtime-contract.md" in docs_index
    assert (
        "docs/architecture/core-runtime-contract.md" in adr
        or "../architecture/core-runtime-contract.md" in adr
    )


def test_console_design_contract_uses_google_design_md_shape() -> None:
    design = read("docs/console/DESIGN.md")

    assert design.startswith("---\n")
    for token in [
        "version: alpha",
        "name: Mery Console",
        "colors:",
        "typography:",
        "rounded:",
        "spacing:",
        "components:",
        "panel:",
        "button-primary:",
        "diagnostic-row:",
        "developer-panel:",
    ]:
        assert token in design

    ordered_sections = [
        "## Overview",
        "## Colors",
        "## Typography",
        "## Layout",
        "## Elevation & Depth",
        "## Shapes",
        "## Components",
        "## Do's and Don'ts",
        "## Mery Console Engineering Extensions",
    ]
    positions = [design.index(section) for section in ordered_sections]
    assert positions == sorted(positions)

    for rule in [
        "Do not call raw `fetch` from feature components.",
        "Generated OpenAPI output lives under `web/console/src/api/generated/`.",
        "Runtime users must not need Node.js.",
        "console-check",
        "axe accessibility checks",
    ]:
        assert rule in design


def test_console_docs_and_agent_guidance_link_design_contract() -> None:
    console_readme = read("docs/console/README.md")
    docs_index = read("docs/README.md")
    agents = read("AGENTS.md")

    assert "DESIGN.md" in console_readme
    assert "Console UI work must follow `docs/console/DESIGN.md`" in agents
    assert "console/DESIGN.md" in docs_index


def test_react_console_scaffold_has_tooling_source_and_quality_gates() -> None:
    package_json = read("web/console/package.json")

    for snippet in [
        "vite",
        "react",
        "typescript",
        "vitest",
        "biome",
        "dependency-cruiser",
        "knip",
        "@axe-core/playwright",
        "console-check",
        "generate:api",
        "check:api",
        "check:fresh",
    ]:
        assert snippet in package_json

    for path in [
        "web/console/index.html",
        "web/console/src/main.tsx",
        "web/console/src/features/app-shell/AppShell.tsx",
        "web/console/src/features/app-shell/__tests__/AppShell.test.tsx",
        "web/console/src/features/developer/DeveloperPanel.tsx",
        "web/console/src/features/developer/__tests__/DeveloperPanel.test.tsx",
        "web/console/src/features/health/HealthPanel.tsx",
        "web/console/src/features/health/__tests__/HealthPanel.test.tsx",
        "web/console/src/features/playground/PlaygroundPanel.tsx",
        "web/console/src/features/playground/__tests__/PlaygroundPanel.test.tsx",
        "web/console/src/features/voices/VoicesPanel.tsx",
        "web/console/src/features/voices/voicesApi.ts",
        "web/console/src/features/voices/__tests__/VoicesPanel.test.tsx",
        "web/console/src/features/voices/__tests__/voicesApi.test.ts",
        "web/console/src/shared/api/meryApi.ts",
        "web/console/src/shared/auth/session.ts",
        "web/console/src/shared/i18n/messages.ts",
        "web/console/src/shared/query/QueryProvider.tsx",
        "web/console/src/test/mocks/handlers.ts",
        "web/console/src/test/mocks/server.ts",
        "web/console/src/api/generated/client.ts",
        "web/console/scripts/generate-openapi-client.mjs",
        "web/console/scripts/check-generated-api-fresh.mjs",
        "web/console/scripts/check-build-fresh.mjs",
        "web/console/playwright.config.ts",
        "web/console/e2e/console-smoke.spec.ts",
    ]:
        assert (ROOT / path).exists(), path


def test_react_console_components_do_not_bypass_api_wrappers() -> None:
    feature_sources = [
        ROOT / "web/console/src/features/app-shell/AppShell.tsx",
        ROOT / "web/console/src/features/developer/DeveloperPanel.tsx",
        ROOT / "web/console/src/features/health/HealthPanel.tsx",
        ROOT / "web/console/src/features/playground/PlaygroundPanel.tsx",
        ROOT / "web/console/src/features/voices/VoicesPanel.tsx",
        ROOT / "web/console/src/features/voices/voicesApi.ts",
    ]

    for source_path in feature_sources:
        text = source_path.read_text(encoding="utf-8")
        assert "fetch(" not in text
        assert "@api/generated" not in text

    wrapper = read("web/console/src/shared/api/meryApi.ts")
    generated = read("web/console/src/api/generated/client.ts")

    assert "@api/generated/client" in wrapper
    assert "fetch(`${basePath}${path}`" in generated
    assert "Authorization: `Bearer ${token}`" in generated


def test_react_console_voices_tracer_bullet_covers_auth_locale_and_governance() -> None:
    app_shell = read("web/console/src/features/app-shell/AppShell.tsx")
    voices_panel = read("web/console/src/features/voices/VoicesPanel.tsx")
    voices_api_test = read("web/console/src/features/voices/__tests__/voicesApi.test.ts")
    panel_test = read("web/console/src/features/voices/__tests__/VoicesPanel.test.tsx")

    messages = read("web/console/src/shared/i18n/messages.ts")
    query_provider = read("web/console/src/shared/query/QueryProvider.tsx")
    generated = read("web/console/src/api/generated/client.ts")
    wrapper = read("web/console/src/shared/api/meryApi.ts")
    handlers = read("web/console/src/test/mocks/handlers.ts")
    app_shell_test = read("web/console/src/features/app-shell/__tests__/AppShell.test.tsx")

    assert "Bearer token" in messages
    assert "Remember on this device" in messages
    assert "Log out" in messages
    assert "clearSession" in app_shell
    assert "MeryQueryProvider" in read("web/console/src/main.tsx")
    assert "QueryClientProvider" in query_provider
    assert "useQuery" in voices_panel
    assert "useMutation" in voices_panel
    assert "Locale filter" in messages
    assert "Search voices" in messages
    assert "Sort voices" in messages
    assert "governanceLabel" in voices_panel
    assert "startVoiceInstall" in generated
    assert "getInstallJob" in generated
    assert "startInstall" in wrapper
    assert "getInstallJob" in wrapper
    assert "getHealth" in wrapper
    assert "runSpeechSmoke" in wrapper
    assert "http.get(\"/v1/catalog/voices\"" in handlers
    assert "http.post(\"/v1/models/install\"" in handlers
    assert "http.get(\"/v1/health\"" in handlers
    assert "http.post" in handlers
    assert "\"/v1/audio/speech\"" in handlers
    assert "allowed (stock)" in voices_api_test
    assert "gated (reference)" in panel_test
    assert "Install succeeded." in panel_test
    assert "vi-VN" in panel_test
    assert "clears remembered token on logout" in app_shell_test


def test_react_console_quality_and_developer_mode_contracts() -> None:
    app_shell = read("web/console/src/features/app-shell/AppShell.tsx")
    health = read("web/console/src/features/health/HealthPanel.tsx")
    playground = read("web/console/src/features/playground/PlaygroundPanel.tsx")
    developer = read("web/console/src/features/developer/DeveloperPanel.tsx")
    playwright = read("web/console/e2e/console-smoke.spec.ts")
    package_json = read("web/console/package.json")

    assert "User Mode navigation" in app_shell
    assert "<HealthPanel" in app_shell
    assert "<PlaygroundPanel" in app_shell
    assert "<DeveloperPanel" in app_shell
    assert "api.getHealth" in health
    assert "api.runSpeechSmoke" in playground
    assert "Pull-based diagnostics only" in developer
    assert "must stay redacted" in developer
    assert "AxeBuilder" in playwright
    assert "@a11y" in playwright
    assert "playwright test" in package_json
    assert "@axe-core/playwright" in package_json
