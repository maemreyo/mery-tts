# Capability readiness contract

ADR-0048 P1 exposes a machine-readable capability/readiness summary for launcher, Console, generic `/v1` clients, support bundles, and local help. The contract is additive and client-neutral: no backend behavior is specific to Zam Reader.

## Schema

Launcher readiness includes `data.capability_readiness` with `schema_version: capability-readiness-v1`.

Required top-level fields:

- `version_layers`: app, API major, catalog schema, voice-pack manifest, and provider-capability versions.
- `auth_state_class`: coarse auth state such as `configured` or `missing`; tokens are never disclosed.
- `installed_voice_count`, `installed_voice_locales`, `catalog_voice_locales`.
- `provider_runtime_availability`: provider runtime class such as `available`, `degraded`, or `unavailable`.
- `openai_speech`: non-streaming `/v1/audio/speech` support.
- `streaming`: streaming support metadata; streaming is supported but secondary for P1 acceptance messaging.
- `storage_advisory`: writable and available-byte hints.
- `pairing`: pairing state without long-lived token disclosure.
- `blocking_readiness_failures`: doctor/readiness checks that are `warn` or `fail`.
- `recovery_actions`: stable user-facing recovery actions.
- `recovery_action_contract`: vocabulary metadata for compatibility.

## Recovery action contract

Recovery actions use `schema_version: recovery-action-v1` and `contract: stable_additive`. Clients should render recovery actions for user guidance and treat lower-level error codes as developer/detail diagnostics.

Stable fields:

- `blocker`
- `recommended_action`
- `title`
- `user_message`
- optional `command`
- optional sanitized `detail`

New blockers or recommended actions may be added over time. Clients must ignore unknown additive fields and should fall back to `title`/`user_message` when they do not recognize a blocker.

## Product boundary

The generic `/v1` client contract remains the product boundary. Zam Reader can consume the same manifest as a reference client, but Mery must not add Zam Reader-only backend behavior.
