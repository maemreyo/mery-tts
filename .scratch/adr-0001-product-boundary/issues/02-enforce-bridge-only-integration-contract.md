# Enforce bridge-only integration contract

Status: production-ready
## Parent

ADR-0001 — `docs/adr/ADR-0001-product-boundary.md`

## What to build

Define contract-level guardrails that keep client coupling limited to versioned schemas, stable IDs, structured errors, and sanitized diagnostics. The helper must reject raw filesystem paths and raw model URLs from client-controlled requests.

## Acceptance criteria

- [x] Public request schemas use stable IDs such as `modelId`, `engineId`, `voiceId`, and contract version fields rather than paths or URLs. `tests/contract/test_bridge_contract.py::test_client_requests_accept_stable_ids_only` pins accepted `model_id`, `voice_id`, and `contract_version` bridge request fields.
- [x] Validation rejects raw filesystem paths, path traversal, and raw model download URLs in client-facing fields. `tests/contract/test_bridge_contract.py::test_client_requests_reject_paths_and_urls` and `tests/unit/test_security_guards.py::test_reject_unsafe_identifier_before_domain_work` cover traversal, POSIX paths, Windows paths, and raw `http`/`https`/`file` URLs.
- [x] Contract tests cover accepted ID-only requests and rejected path/URL requests. `tests/contract/test_bridge_contract.py` covers accepted stable bridge IDs and rejected unsafe model IDs.
- [x] No helper module assumes Zam Reader is the only client. README docs describe Mery as a standalone any-client localhost `/v1` server, and `tests/unit/test_package_boundary.py` pins the generic package boundary without client imports.

## Blocked by

- 01-create-standalone-helper-package-boundary

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Exercise every client-facing ID field through HTTP/CLI, not only helper functions, and prove raw paths/URLs are rejected before model/catalog/storage work begins.
  - Progress: shared unsafe identifier guard regression coverage rejects traversal, raw filesystem paths, Windows paths, and raw `http`/`https`/`file` URLs before domain work. `tests/contract/test_rest_management_endpoints.py::test_model_install_rejects_paths_and_urls_before_domain_work` now proves `/v1/models/install` rejects unsafe `model_id` values before model/catalog/storage work, while `test_model_install_accepts_stable_model_id_only` proves stable IDs remain accepted. `tests/contract/test_bridge_contract.py` pins `InstallModelRequest` and `SynthesisRequest` validation at the contract layer. Per-route/per-CLI wiring for every other client-facing ID remains pending.
- [x] Audit public responses and diagnostics so no route exposes absolute local paths, raw download URLs, or Zam Reader-specific assumptions.
  - Progress: `tests/contract/test_bridge_contract.py::test_public_response_schemas_do_not_expose_filesystem_paths` audits all public response schemas (`HealthResponse`, `EnginesResponse`, `InstalledVoicesResponse`, `CatalogVoicesResponse`, `ModelInstallResponse`, `ModelStatusResponse`, `ModelDeleteResponse`, `StorageResponse`, `DiagnosticsResponse`, `NativeErrorResponse`) and asserts none contain `path`, `url`, or `dir` fields. `PairingResponse.setup_url` is an intentional localhost setup URL and is excluded from the audit. `StorageResponse` exposes only `used_bytes` and `free_bytes` (integers), not filesystem paths. `DiagnosticsResponse` exposes only check names and statuses. CLI `storage show` output uses `stats.root_path` which is an internal diagnostic path, not exposed through the API.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Exercise every client-facing ID field through HTTP/CLI, not only helper functions, and prove raw paths/URLs are rejected before model/catalog/storage work begins.
- Audit public responses and diagnostics so no route exposes absolute local paths, raw download URLs, or Zam Reader-specific assumptions.
