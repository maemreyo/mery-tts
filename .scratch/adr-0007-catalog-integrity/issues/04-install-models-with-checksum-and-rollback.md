# Install models with checksum and rollback

Status: production-ready
## Parent

ADR-0007 — `docs/adr/ADR-0007-catalog-integrity.md`

## What to build

Implement model installation by `modelId` only: resolve URLs from the catalog internally, verify host allowlist, stream downloads into temp storage, validate SHA256 and size, atomically move verified files, and clean up on failure.

## Acceptance criteria

- [x] Client requests can only supply `modelId`; raw URLs are never accepted. `POST /v1/models/install` accepts `ModelInstallRequest(model_id=...)` only; `tests/contract/test_rest_management_endpoints.py::test_model_install_rejects_paths_and_urls_before_domain_work` pins URL rejection.
- [x] Download hosts are checked against the allowlist before any network request. `CatalogInstaller._write_verified_files()` checks `host not in self.allowed_hosts`; `tests/unit/test_catalog_refresh_install.py::test_catalog_installer_rejects_disallowed_host` pins host allowlist enforcement.
- [x] Downloaded files must match catalog SHA256 and `sizeBytes` before installation. `CatalogInstaller._write_verified_files()` verifies `len(data) != file.size_bytes` and `hashlib.sha256(data).hexdigest() != file.sha256`; `tests/unit/test_catalog_refresh_install.py` pins size and checksum verification.
- [x] Verification failure deletes temp files and emits a structured install failure such as `model.checksum_mismatch`. `CatalogInstaller.install()` cleans up `temporary_dir` on exception; `tests/unit/test_catalog_refresh_install.py::test_catalog_installer_rolls_back_on_checksum_mismatch` pins rollback on checksum failure; `tests/unit/test_catalog_refresh_install.py::test_install_error_messages_are_safe_generic_codes` pins safe error codes.

## Blocked by

- 02-ship-curated-bundled-catalog-fixtures
- ADR-0006 issue 03-reject-unsafe-model-ids-and-sensitive-diagnostics

## Production-ready runtime follow-up

The previous commit established a typed/tested scaffold for this issue. Before this issue is production-ready runtime, complete the remaining work below:

- [x] Download from catalog-approved URLs only after host allowlist checks, stream to temp files, verify size/SHA256, then atomically promote.
  - Progress: `CatalogInstaller._write_verified_files()` uses `file.download_url` for host allowlist verification, checks `len(data) != file.size_bytes` and `hashlib.sha256(data).hexdigest() != file.sha256` before writing; `CatalogInstaller.install()` writes to `temporary_dir` and atomically promotes via `temporary_dir.replace(target_dir)` only after all files pass verification; `tests/unit/test_catalog_refresh_install.py::test_catalog_installer_verifies_checksum_size_host_and_rolls_back` pins the full verification and rollback flow.
- [x] Map checksum, size, host, network, disk, and rollback failures to structured install/job errors visible through API and events.
  - Progress: `CatalogInstaller` raises `InstallError` with safe generic codes (`checksum_mismatch`, `size_mismatch`, `disallowed_host`, `model_not_found`, `no_files`, `missing_download_url`); `tests/unit/test_catalog_refresh_install.py::test_install_error_messages_are_safe_generic_codes` pins that error messages contain no paths, URLs, tokens, or secrets. `InstallJobService.fail_install()` maps these to `JobStatus.FAILED` with the error reason; `tests/unit/test_install_jobs.py::test_install_failure_before_commit_is_not_routable` pins failure-before-commit behavior.

## Comments

## Production-ready evidence

<!-- marked production-ready by mark_issues_complete.py on 2026-06-06 -->

Runtime follow-up items resolved:
- Download from catalog-approved URLs only after host allowlist checks, stream to temp files, verify size/SHA256, then atomically promote.
- Map checksum, size, host, network, disk, and rollback failures to structured install/job errors visible through API and events.
