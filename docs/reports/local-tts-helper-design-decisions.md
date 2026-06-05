# Local TTS Helper — Design Decision Log

**Date started:** 2026-06-05
**Purpose:** Portable decision log for a standalone Local TTS Helper app that Zam Reader can bridge to.
**Context:** User wants local TTS to be easy to install and manage from the extension/add-on, while keeping the system flexible, clean, modular, standalone, scalable, and well-tested.

This document records each grill decision as a verdict so the design can be lifted into a separate app implementation later.

---

## Decision 1 — Product/ownership boundary

**Question:** Should the feature be an extension-managed companion local TTS helper, or should the extension own/install the whole TTS engine and model runtime?

**Verdict:** Use an **extension-managed companion local TTS helper**.

**Rationale:**

- Browser extensions should not own native executable installation directly.
- A companion helper keeps Zam Reader store-reviewable and self-contained.
- The helper owns native binaries, models, engines, cache, checksums, and local playback services.
- Zam Reader owns UI, provider selection, status display, fallback, and bridge calls.
- This is the cleanest SoC boundary.

**Architecture implication:**

```text
Zam Reader extension
  -> LocalTTSProvider
  -> LocalTTSBridge
  -> Companion Local TTS Helper
  -> EngineRegistry / ModelManager / VoiceRegistry
```

---

## Decision 2 — Helper shape

**Question:** Should the helper be CLI-first, daemon/server-first, or hybrid?

**Verdict:** Use a **hybrid helper**.

**Rationale:**

- CLI-first enables standalone testing, debugging, support, and CI.
- Daemon/server mode enables low-latency playback, warm models, streaming, and extension UX.
- A hybrid helper can expose both:
  - CLI commands for humans/tests.
  - Runtime API for Zam Reader.

**Architecture implication:**

```text
zam-tts ping
zam-tts voices
zam-tts models
zam-tts speak
zam-tts doctor

helper daemon/server
  -> health/status
  -> voices/models
  -> synthesize/stream
  -> install/delete/verify models
```

---

## Decision 3 — Product architecture priority

**Question:** Optimize for store-compliant product architecture, fastest proof-of-concept, or browser-only/no-helper architecture?

**Verdict:** Optimize for **store-compliant product architecture**.

**Rationale:**

- The long-term target is a real product-quality helper, not only a developer demo.
- Native/local runtime is distributed separately and explicitly installed by the user.
- The extension stays clean and reviewable.
- The helper remains independently testable and distributable.

**Implementation strategy:** Use a fast local helper transport first if needed, but do not compromise the architectural boundary.

---

## Decision 4 — Transport architecture

**Question:** Should Zam Reader talk to the helper via Native Messaging, localhost HTTP/WebSocket, or a hybrid transport abstraction?

**Verdict:** Use a **hybrid transport abstraction**, with **localhost HTTP/WebSocket first**.

**Rationale:**

- Localhost HTTP/WebSocket is easier to develop, test, inspect, and reuse by CLI/app/other clients.
- Native Messaging is more store-canonical and avoids open ports, but is harder to install/debug because browser-specific manifests and extension IDs differ.
- A transport abstraction prevents Zam Reader from depending directly on either transport.

**Architecture implication:**

```text
LocalTTSBridge
  -> LocalhostTransport        # v1 implementation
  -> NativeMessagingTransport  # future implementation
```

**Hard rule:** Reader UI/content code must never call `fetch("http://127.0.0.1:...")` directly. Calls go through provider -> bridge -> transport.

---

## Decision 5 — Initial scope of local-helper integration

**Question:** Should v1 support playback/synthesis only, or full model management immediately?

**Verdict:** Support **full model management immediately**.

**Rationale:**

- User needs people to easily install and manage local TTS from the extension/add-on.
- A playback-only bridge would not solve the product problem.
- The feature is a Local TTS Management System, not merely a synthesize endpoint.

**Scope implication:**

Zam Reader should support:

- Detect helper.
- Show helper health/status.
- List engines.
- List installed voices/models.
- List curated catalog voices/models.
- Install/download models.
- Show install progress.
- Verify model integrity.
- Select voice/model.
- Synthesize/play/stop.
- Delete model/cache.
- Run diagnostics/doctor checks.
- Fall back to Web Speech.

**SoC rule:** The helper owns downloads, cache paths, checksums, and model verification. The extension owns UI/orchestration only.

---

## Decision 6 — Model catalog source

**Question:** Should model catalogs be bundled in Zam Reader, owned by helper, remote-only, or hybrid?

**Verdict:** Use a **hybrid catalog**.

**Rationale:**

- Zam Reader/helper should ship a small curated minimum catalog for deterministic tests and reliable first-run UX.
- The helper can support an explicit user-triggered remote catalog refresh later.
- Remote refresh must be opt-in and transparent because it performs network access.
- This balances offline friendliness with catalog evolution.

**Architecture implication:**

```text
Bundled curated catalog
  -> English recommended voices
  -> Vietnamese recommended voices
  -> known sizes/checksums/licenses

Optional refresh catalog
  -> explicit user action
  -> remote source URL
  -> versioned catalog schema
  -> checksum/signature validation
```

**Privacy/network implication:**

Reading/synthesis remains local. Model/catalog download is a separate explicit setup action and must not be confused with zero-network reading behavior.

---

## Decision 7 — Helper implementation language/runtime

**Question:** Should the standalone helper be implemented in Rust, Python, Node/Electron, or a hybrid runtime?

**Verdict:** Use a **Python-first standalone helper**, with strict modular/product guardrails.

**Rationale:**

- User is more comfortable with Python than Rust.
- Python has the strongest immediate ecosystem for Kokoro, Piper wrappers, Hugging Face/model downloads, audio processing, FastAPI/WebSocket servers, and packaging experiments.
- Development velocity matters because this is a separate helper app and needs fast product validation.
- Rust remains attractive for a future rewrite or a thin native host, but forcing Rust now would slow design and implementation.

**Guardrails:**

- Python must be treated as a real app runtime, not loose scripts.
- Use a typed package layout with clear modules: `api`, `engines`, `models`, `catalog`, `audio`, `diagnostics`, `settings`, `cli`.
- Keep engine-specific dependencies behind adapters so the core does not become a Kokoro/Piper monolith.
- Provide a CLI (`zam-tts`) and server mode from the same package.
- Use contract tests for the bridge API so Zam Reader is not coupled to Python internals.
- Packaging must be solved explicitly later: uv/standalone bundle first, then signed/notarized macOS app or pkg when productizing.

**Architecture implication:**

```text
zam-local-tts-helper/          # separate app/repo/package candidate
  src/zam_tts/
    api/                       # FastAPI/WebSocket or HTTP routes
    bridge_contract/           # versioned request/response schemas
    engines/                   # PiperPlusEngine, KokoroEngine, MacSayEngine
    models/                    # install/delete/verify/cache
    catalog/                   # bundled + remote catalog support
    audio/                     # playback/export/stream chunks
    diagnostics/               # doctor checks and structured errors
    settings/                  # helper config paths and persistence
    cli/                       # zam-tts commands
```

---

## Decision 8 — Initial engine strategy

**Question:** Should the helper ship Piper-plus first, Kokoro first, dual-engine from day one, or plugin architecture with one initial engine?

**Verdict:** Ship **at least two providers from day one**: Piper-plus and Kokoro.

**Rationale:**

- Supporting two engines immediately forces the architecture to be genuinely modular instead of pretending to be modular around a single implementation.
- Piper-plus covers the lightweight/offline/fast path.
- Kokoro covers the higher-quality English/more natural voice path and matches many OSS local-helper examples.
- A dual-provider baseline lets Zam Reader expose meaningful choices: `lightweight` vs `quality`.
- This better satisfies the user's goals: flexible, clean, SoC, modular, standalone, scalable, and well-tested.

**Guardrails:**

- Do not create engine-specific branching in the API surface.
- Do not let Zam Reader know Piper/Kokoro internals.
- Both engines must implement the same engine adapter contract.
- Engine dependencies must be isolated so a Kokoro failure does not break Piper-plus.
- Tests must run adapter contract tests against both providers.
- Model catalog entries must declare `engineId`, required files, checksum, size, language, quality tier, and capabilities.

**Architecture implication:**

```text
EngineRegistry
  -> piper-plus
     -> fast CPU path
     -> small models
     -> multilingual/Vietnamese candidate
  -> kokoro
     -> quality English path
     -> natural voices
     -> larger model/cache footprint
```

**Provider positioning:**

| Provider | Product label | Primary use |
|---|---|---|
| `piper-plus` | Lightweight local voice | Fast, low-RAM, multilingual/offline path |
| `kokoro` | Quality local voice | More natural English listening path |

---

## Decision 9 — Local API protocol shape

**Question:** Should the helper API be REST-only, WebSocket-first, or a hybrid protocol?

**Verdict:** Use a **hybrid protocol**: REST for deterministic CRUD/status operations, WebSocket for streaming/progress/events.

**Rationale:**

- REST is ideal for health checks, engine listing, voice/model catalog reads, model delete, storage usage, settings, and diagnostics.
- REST is easy to test with `curl`, easy to document, and fits contract-test snapshots.
- WebSocket is ideal for long-running operations: synthesis streaming, model install progress, cancellation, status events, and future warm-session playback.
- A hybrid protocol preserves clear separation of concerns instead of overloading one transport style.
- It keeps the helper standalone and testable: REST contract tests can run without audio streaming, while WebSocket tests cover event sequencing.

**Protocol split:**

```text
REST
  GET    /v1/health
  GET    /v1/engines
  GET    /v1/voices/installed
  GET    /v1/catalog/voices
  POST   /v1/models/install
  DELETE /v1/models/{modelId}
  GET    /v1/models/install/{jobId}
  GET    /v1/storage
  GET    /v1/diagnostics

WebSocket
  /v1/events
    -> install.progress
    -> synthesize.started
    -> audio.chunk
    -> audio.done
    -> synthesize.cancelled
    -> helper.statusChanged
```

**Versioning rule:**

- Every API path is versioned under `/v1`.
- Every WebSocket event includes `type`, `schemaVersion`, `requestId`, and `timestamp`.
- Zam Reader depends on the bridge contract schemas, not on FastAPI/Kokoro/Piper internals.

**Testing implication:**

- REST endpoints get schema contract tests and golden response fixtures.
- WebSocket gets event-order contract tests for install progress, synthesize stream, cancellation, and helper crash/reconnect behavior.

---

## Decision 10 — Audio delivery mode

**Question:** Should the helper play audio directly, should Zam Reader play streamed audio, or should audio delivery be hybrid?

**Verdict:** Use **hybrid audio delivery**.

**Rationale:**

- The helper must support direct playback for standalone CLI/manual testing: `zam-tts speak --play`.
- Zam Reader should control playback for product UX: pause, stop, progress, highlighting, follow mode, reader state, and future karaoke/word-boundary behavior.
- Streaming audio back to the extension keeps UI state and audio state in one place.
- Direct helper playback alone would make the extension blind to real playback timing and failure states.
- Hybrid delivery preserves standalone helper testability without compromising Reader UX.

**Mode split:**

```text
Helper CLI/manual mode
  zam-tts speak --text "Hello" --play
  -> helper plays through system audio

Zam Reader mode
  extension -> /v1/events WebSocket synthesize request
  helper -> audio.chunk/audio.done events
  extension -> Web Audio/offscreen/content playback
```

**Architecture implication:**

- `AudioRenderer` belongs to Zam Reader for extension playback.
- `AudioOutput` belongs to the helper for CLI/debug playback.
- Both consume the same synthesized audio stream/result contract.
- Helper must not assume it owns speakers during extension sessions.

**Testing implication:**

- Helper unit/integration tests verify generated audio metadata and CLI playback command paths.
- Zam Reader bridge tests verify chunk buffering, stop/cancel, stream completion, and fallback behavior.
- Manual QA must include both `zam-tts speak --play` and extension-triggered playback.

---

## Decision 11 — Install/setup UX surface

**Question:** Should install/setup live primarily in the Options page, Reader Audio Panel, Companion app UI, or a layered UX across all three?

**Verdict:** Use a **layered install/setup UX**.

**Rationale:**

- The Reader Audio Panel should stay lightweight and contextual: it tells the user local voices are available/missing and offers a clear setup path.
- The Options page should own full extension-side management: helper status, provider selection, catalog, model install/delete, storage usage, and diagnostics.
- The standalone companion app/CLI should own native-level recovery: service start/stop, doctor checks, cache repair, binary/model path issues, logs, and uninstall instructions.
- This avoids turning the Reader overlay into a package manager while still making setup discoverable at the moment of need.
- It preserves SoC between reading UX, extension configuration, and native/helper operations.

**Surface split:**

```text
Reader Audio Panel
  -> current provider/status
  -> selected voice/model
  -> local helper missing/available badge
  -> CTA: "Set up local voices"
  -> fallback to Web Speech

Options Page
  -> full helper connection status
  -> engine/provider list
  -> installed voices/models
  -> curated catalog
  -> install/delete/update/verify models
  -> storage usage
  -> diagnostics summary

Companion App / CLI
  -> start/stop helper
  -> doctor checks
  -> logs
  -> native dependency checks
  -> cache repair
  -> manual model path/debug commands
  -> uninstall instructions
```

**Testing implication:**

- Audio Panel tests cover missing-helper, installed-helper, selected-provider, fallback, and CTA states.
- Options tests cover catalog rendering, install progress, delete confirmation, storage usage, and diagnostics.
- Helper CLI tests cover `doctor`, `ping`, `models`, `voices`, `speak --play`, and failure recovery.

---

## Decision 12 — Localhost transport security model

**Question:** Should localhost transport use only loopback binding, an auth token, origin allowlist, or a full security combo?

**Verdict:** Use the **full localhost security combo**.

**Rationale:**

- Binding to localhost alone is not enough; local webpages and local apps can still attempt requests if they discover the port.
- Product-grade helper architecture must treat localhost as an IPC surface, not as trusted internal code.
- The helper should be standalone and safe even if used by clients besides Zam Reader.
- A layered security model makes future Native Messaging migration cleaner because authentication/authorization is already explicit at the bridge boundary.

**Required controls:**

```text
Network binding
  -> bind only to 127.0.0.1 / ::1
  -> never bind 0.0.0.0 by default

Port management
  -> use a per-install random port or configurable fixed port with explicit user opt-in
  -> persist port in helper config
  -> expose port to Zam Reader only through setup/pairing

Authentication
  -> generate per-install auth token
  -> require token on every REST request and WebSocket connection
  -> support token rotation from companion app/CLI

Origin/CORS
  -> allow only configured extension origins/IDs
  -> reject browser origins not in allowlist
  -> do not use wildcard CORS

Request hardening
  -> request size limits
  -> text length limits
  -> rate limits for synthesize/model operations
  -> no arbitrary file path reads/writes from extension requests
  -> model IDs only, never raw filesystem paths from browser

Observability
  -> structured security diagnostics
  -> log rejected origin/auth/rate-limit events without storing user text
```

**API implication:**

- Zam Reader's `LocalhostTransport` must attach auth metadata automatically.
- UI should display connection status without exposing the token.
- Pairing/setup flow must establish the token and port deliberately.

**Testing implication:**

- Contract tests must include missing-token, bad-token, wrong-origin, oversized-request, too-long-text, rate-limit, and raw-path-rejection scenarios.
- Security tests must prove user text is not persisted in logs.

---

## Decision 13 — Model/cache storage and quota UX

**Question:** Should model/cache storage use a helper-owned app data directory, a user-selectable model directory, or a hybrid model?

**Verdict:** Use **hybrid storage**: helper-owned app data directory by default, with an advanced user override managed by the companion app/CLI.

**Rationale:**

- Default storage must be predictable, safe, and zero-configuration for normal users.
- Model files can grow large, so advanced users need a supported way to move models/cache to another folder or volume.
- The helper should own filesystem paths; Zam Reader should never send or manipulate raw paths.
- A helper-owned default keeps security and tests deterministic.
- An advanced override keeps the standalone helper scalable beyond a single small model set.

**Default macOS layout:**

```text
~/Library/Application Support/Zam Local TTS/
  config.json
  catalog/
    bundled-catalog.json
    remote-catalog.json
  models/
    piper-plus/
    kokoro/
  cache/
    downloads/
    temp/
  logs/
    helper.log
  diagnostics/
```

**UX rules:**

- Zam Reader Options page shows storage usage, installed models, model sizes, and delete actions.
- Zam Reader does not expose raw filesystem paths in normal UI.
- Companion app/CLI provides advanced commands for changing model directory and repairing/migrating cache.
- If storage is low, helper reports structured diagnostics; extension presents actionable UI.
- Delete operations use model IDs only, never paths.

**CLI implication:**

```text
zam-tts storage show
zam-tts storage move --to <directory>
zam-tts storage repair
zam-tts models delete <modelId>
```

**Testing implication:**

- Tests must cover default path resolution, custom path config, migration, low-disk diagnostic, delete-by-model-id, path traversal rejection, and cache repair.

---

## Decision 14 — Catalog/model integrity policy

**Question:** Should model integrity use checksums only, signed catalog only, signed catalog plus checksums, or signed catalog plus checksums plus download host allowlist?

**Verdict:** Use **signed/versioned catalog + per-file checksums + download host allowlist**.

**Rationale:**

- Model management is a security boundary because the helper downloads files onto the user's machine.
- A signed catalog proves the catalog metadata came from a trusted maintainer.
- Per-file SHA256 and size metadata prove each downloaded model/config file matches the catalog.
- A download host allowlist prevents the helper from becoming an arbitrary remote file downloader.
- License metadata keeps the helper/product honest about redistribution and model usage.
- This design is standalone and testable: catalog verification can be tested without Zam Reader.

**Catalog requirements:**

Each catalog must include:

```text
catalogId
schemaVersion
catalogVersion
createdAt
expiresAt or refreshPolicy
signature
models[]
  modelId
  engineId
  displayNameKey / label
  language
  locale
  qualityTier
  capabilities
  files[]
    url
    sha256
    sizeBytes
    fileRole          # model, config, voices, tokenizer, dictionary, etc.
  license
  source
  recommendedFor[]   # lightweight, quality, vietnamese, english, etc.
```

**Download rules:**

- Only allowlisted hosts may be used by default.
- Every file must match expected SHA256 and size.
- Downloads go to temp cache first, then atomic move into model store after verification.
- Failed verification deletes the temp file and records a diagnostic.
- Extension requests install by `modelId`; helper resolves URLs internally.
- Remote catalog refresh is explicit user action, not silent background behavior.

**Testing implication:**

- Tests must cover valid signature, invalid signature, expired catalog, wrong checksum, wrong size, non-allowlisted host, interrupted download, resume/retry behavior, and atomic install rollback.

---

## Decision 15 — Cross-browser support order

**Question:** Should local TTS support start Firefox-only, Chrome-first, or dual Firefox + Chrome from the first contract layer?

**Verdict:** Design **dual Firefox + Chrome from the first contract layer**, while allowing UX rollout to remain Firefox-first.

**Rationale:**

- Zam Reader is Firefox-first, but explicitly targets Chrome/Edge/Brave/Cốc Cốc too.
- Helper bridge, API schemas, auth model, provider registry, and tests should not encode Firefox-only assumptions.
- Cross-browser transport/audio differences are easier to handle behind abstractions early than to retrofit later.
- UX polish can still ship Firefox-first without compromising architecture.
- This supports flexible, clean, modular, standalone, scalable, and well-tested design.

**Browser strategy:**

```text
Contract layer
  -> Firefox + Chromium from day one

Zam Reader UX rollout
  -> Firefox-first
  -> Chromium validated by contract/e2e smoke tests
  -> Edge/Brave/Cốc Cốc treated as Chromium compatibility targets

Future Native Messaging transport
  -> Firefox uses allowed_extensions
  -> Chromium uses allowed_origins
  -> transport abstraction hides this from TTS provider/UI
```

**Testing implication:**

- Contract tests must run browser-agnostic.
- Extension bridge tests must cover Firefox and Chromium behavior where APIs differ.
- Manifest/permission generation must be tested for both Firefox and Chromium targets.
- Audio playback strategy must not rely solely on Chrome-only APIs unless there is a Firefox fallback.

---

## Decision 16 — Test matrix and CI strategy

**Question:** Should testing focus only on the helper, only on the extension, or use a full layered test pyramid across helper, bridge, engines, API, browser, and manual QA?

**Verdict:** Use a **full layered test pyramid**.

**Rationale:**

- This feature crosses several risky boundaries: browser extension, localhost transport, auth, Python helper, model catalog, model downloads, engine adapters, streaming audio, and browser playback.
- Testing only the helper misses extension permission, UI, fallback, and playback issues.
- Testing only the extension misses protocol drift, model install failures, engine failures, and streaming bugs.
- A layered pyramid keeps the standalone helper independently shippable while proving Zam Reader integration remains stable.
- This is necessary for flexible, clean, modular, standalone, scalable, and well-tested architecture.

**Required test layers:**

```text
Helper package
  -> unit tests for catalog/model/cache/settings/security utilities
  -> engine adapter contract tests for piper-plus and kokoro
  -> model install/delete/verify tests with fixture catalog
  -> CLI tests: ping, doctor, voices, models, speak --dry-run/play path

Helper API
  -> REST schema contract tests
  -> WebSocket event-order tests
  -> auth/origin/rate-limit/request-size security tests
  -> helper crash/restart/reconnect tests

Zam Reader extension
  -> LocalTTSBridge tests with fake helper
  -> provider registry tests for installed/missing/degraded local provider
  -> UI state tests for Audio Panel and Options page
  -> fallback tests to Web Speech

Integration
  -> real helper + Zam Reader bridge smoke tests
  -> model install with tiny fixture model or mocked download server
  -> synthesize stream/cancel/complete scenarios

Browser e2e
  -> Firefox smoke test
  -> Chromium smoke test
  -> extension playback and fallback behavior

Manual QA
  -> install helper
  -> pair extension
  -> install Piper-plus model
  -> install Kokoro model
  -> synthesize via helper CLI
  -> synthesize via extension
  -> stop/cancel
  -> delete model
  -> rotate token
  -> uninstall/reinstall helper
```

**CI implication:**

- Helper repo/package should have its own CI independent of Zam Reader.
- Zam Reader should run fake-helper tests in normal CI.
- Real-helper integration can run as scheduled/nightly or tagged job to avoid heavy model downloads on every commit.
- Browser e2e should use small fixture responses for normal CI and real synthesis only in explicit integration jobs.

---

## Decision 17 — Python helper packaging/distribution strategy

**Question:** Should Python helper distribution start as uv/pipx/dev CLI, standalone app/binary, signed installer, or phased packaging?

**Verdict:** Use **budget-aware phased packaging without mandatory signing for v1**.

**Rationale:**

- User does not currently have budget for Apple Developer signing/notarization.
- Requiring signed `.pkg`/`.dmg` would block progress and overfit the design to a paid distribution path too early.
- The helper still needs to be standalone, modular, and testable; lack of signing is not permission for messy packaging.
- Start with developer-friendly installation, then improve packaging as adoption/budget justifies it.
- The architecture must not depend on the packaging method.

**Packaging phases:**

```text
Phase 1 — Developer / early adopter install
  -> uv tool install or pipx install
  -> `zam-tts` CLI available
  -> helper server launched by CLI
  -> clear setup docs

Phase 2 — Unsigned standalone bundle
  -> PyInstaller/Nuitka/Briefcase-style app or executable
  -> user may need right-click Open / quarantine removal instructions
  -> no paid Apple Developer account required

Phase 3 — Optional signed/notarized distribution
  -> only if budget/adoption justifies it
  -> .dmg/.pkg, signed helper, smoother Gatekeeper UX
```

**Hard constraints:**

- The helper app must remain packaging-agnostic internally.
- CLI, API, engine adapters, model manager, catalog verifier, and tests must work the same in all packaging phases.
- Zam Reader setup UI must clearly distinguish supported early-adopter install from polished signed app install.
- Unsigned app instructions must be honest and safe; do not hide Gatekeeper implications.

**Recommended v1 install options:**

```text
uv tool install zam-local-tts-helper
# or
pipx install zam-local-tts-helper

zam-tts doctor
zam-tts serve
```

**Testing implication:**

- CI must test the package install path (`uv`/pipx equivalent), CLI entrypoint, server startup, and teardown.
- Packaging smoke tests should verify app/executable mode separately when introduced.

---

## Decision 18 — Pairing/setup flow between extension and helper

**Question:** Should pairing use manual config, helper-printed pairing code, localhost scanning, pairing URL/deep link, or a hybrid pairing code plus setup URL?

**Verdict:** Use **hybrid pairing: helper-printed pairing code plus setup URL**.

**Rationale:**

- Manual host/port/token entry is too error-prone for the desired easy install/manage UX.
- Blind localhost scanning is not clean and creates privacy/security concerns.
- A pairing code gives a clear user-confirmed trust boundary.
- A setup URL improves UX while preserving explicit consent.
- This works with unsigned CLI-first packaging and can later map to a companion app UI.
- Pairing can be tested independently of TTS engines.

**Pairing flow:**

```text
1. User installs helper via uv/pipx.
2. User runs:
     zam-tts pair
3. Helper starts or confirms local server is running.
4. Helper prints:
     - localhost URL
     - one-time pairing code
     - expiration time
5. User opens Zam Reader Options -> Local Voices -> Pair Helper.
6. User pastes code OR opens provided setup URL.
7. Extension exchanges code for port + token + helper identity.
8. Extension stores connection config in browser.storage.local.
9. Helper invalidates one-time code.
10. Extension runs health check and shows connected status.
```

**Security rules:**

- Pairing codes are one-time and short-lived.
- Pairing exchange must bind to localhost only.
- The long-lived auth token is not shown in normal UI.
- Token rotation is supported via CLI/app and extension reconnect flow.
- Failed pairing attempts are rate-limited and logged without user text.

**API implication:**

```text
POST /v1/pair/claim
  input: oneTimeCode, clientInfo
  output: helperId, port, authToken, expiresAt, capabilities
```

**Testing implication:**

- Tests must cover valid code, expired code, reused code, wrong code, rate limit, token storage, token rotation, and helper restart after pairing.

---

## Decision 19 — Error taxonomy and fallback behavior

**Question:** Should helper/bridge errors be simple strings, structured codes, or a full structured taxonomy with fallback policy?

**Verdict:** Use a **full structured error taxonomy with explicit fallback policy**.

**Rationale:**

- Simple error strings are not testable, not stable, and not compatible with Zam Reader's i18n/domain-key discipline.
- The extension must be able to distinguish missing helper, expired token, model missing, model download failed, engine unavailable, synthesis failed, stream interrupted, and browser playback failure.
- Structured errors let Zam Reader choose the correct behavior: retry, fallback to Web Speech, show setup CTA, open diagnostics, or stop safely.
- The helper remains standalone because it can expose the same structured errors to CLI, API clients, logs, and companion UI.

**Error shape:**

```text
LocalTTSError
  code                 # stable machine code, e.g. helper.not_running
  category             # connection | auth | catalog | model | engine | synthesis | playback | storage | security
  severity             # info | warning | error | critical
  recoverability       # automatic | user_action | reinstall_required | unsupported
  userMessageKey       # i18n key for Zam Reader/helper UI
  recommendedAction    # retry | pair_helper | install_model | fallback_web_speech | open_doctor | rotate_token
  fallbackPolicy       # none | web_speech | previous_voice | stop_session
  diagnostic           # sanitized metadata, never raw text
  requestId
  timestamp
```

**Required categories:**

```text
connection
  -> helper.not_running
  -> helper.unreachable
  -> helper.version_incompatible

auth
  -> auth.missing_token
  -> auth.invalid_token
  -> auth.pairing_expired
  -> auth.origin_denied

catalog
  -> catalog.signature_invalid
  -> catalog.expired
  -> catalog.host_not_allowed

model
  -> model.not_installed
  -> model.download_failed
  -> model.checksum_mismatch
  -> model.disk_space_low
  -> model.delete_failed

engine
  -> engine.unavailable
  -> engine.dependency_missing
  -> engine.health_failed

synthesis
  -> synthesis.text_too_long
  -> synthesis.cancelled
  -> synthesis.failed
  -> synthesis.timeout

playback
  -> playback.stream_interrupted
  -> playback.browser_audio_failed

security
  -> security.rate_limited
  -> security.request_too_large
  -> security.path_rejected
```

**Fallback policy:**

- If helper missing/unreachable -> fall back to Web Speech and show setup CTA.
- If selected model missing -> offer install model; fallback to Web Speech or previous installed local voice.
- If synthesis fails once -> retry once if recoverable; then fallback.
- If auth fails -> do not fallback silently; show re-pair action.
- If security error -> no automatic retry; show safe diagnostic.
- If browser audio playback fails -> stop local session and fallback only if safe.

**Testing implication:**

- Tests must snapshot every error shape.
- UI tests must verify each major category maps to the correct i18n key and action.
- Fallback tests must prove Web Speech remains available and local failures do not break the reader.
- Logs must prove no raw user text is stored in diagnostics.

---

## Decision 20 — Provider defaults and user-facing labels

**Question:** Should provider selection be fully manual, auto-pick the best local provider, or use contextual recommended defaults?

**Verdict:** Use **contextual recommended defaults**.

**Rationale:**

- Zam Reader should not silently switch away from Web Speech just because a helper is installed.
- Local TTS setup is explicit opt-in, so provider selection should also be user-confirmed.
- Raw engine names like Piper-plus and Kokoro are useful for advanced users, but normal users need intent-based labels.
- Contextual labels keep the system flexible and scalable as more engines are added.
- This preserves clean SoC: engines expose capabilities; UI maps capabilities to user-facing profiles.

**Default behavior:**

```text
Before setup
  -> default provider: Web Speech
  -> show optional CTA: Set up local voices

After helper paired
  -> keep current provider until user confirms switch
  -> recommend profiles based on installed/catalog voices

Profiles
  -> Lightweight local voice
       engine: piper-plus
       use: fast, low-RAM, multilingual/offline, Vietnamese candidate

  -> Quality local voice
       engine: kokoro
       use: natural English listening

  -> System/browser voice
       engine: Web Speech
       use: zero setup fallback
```

**UI rules:**

- Show intent labels first: `Lightweight`, `Quality`, `System/browser`.
- Show engine names secondarily for transparency: `Powered by Piper-plus`, `Powered by Kokoro`.
- Always show fallback status.
- If selected local provider fails, do not permanently change selection without user confirmation.
- Persist selected provider/model/voice as user preference.

**Testing implication:**

- Tests must cover no-helper default, helper-installed no auto-switch, user-confirmed local switch, missing model recommendation, fallback display, and provider failure without permanent preference mutation.

---

## Decision 21 — MVP cut line vs full v1 acceptance criteria

**Question:** Should the local TTS helper feature be scoped as a small MVP, medium MVP, full v1 management system, or split as medium MVP plus full v1 acceptance?

**Verdict:** Define the target as **full v1 local TTS management**.

**Rationale:**

- User explicitly wants a complete, flexible, clean, modular, standalone, scalable, and well-tested design.
- The feature goal is not merely synthesis; it is easy installation and management from Zam Reader/add-on surfaces.
- A smaller playback-only MVP would not satisfy the product problem.
- The helper is a separate app/module, so the full v1 acceptance must be portable and buildable outside Zam Reader.
- Implementation may still be internally sliced for delivery, but the feature definition should not be reduced.

**Full v1 acceptance scope:**

```text
Standalone helper app/package
  -> Python-first package
  -> CLI + server mode
  -> Piper-plus provider
  -> Kokoro provider
  -> EngineRegistry abstraction
  -> ModelManager
  -> VoiceRegistry
  -> hybrid bundled/remote catalog
  -> signed/versioned catalog verification
  -> per-file checksum/size verification
  -> allowlisted download hosts
  -> helper-owned storage with advanced override
  -> structured diagnostics and doctor command
  -> secure localhost transport
  -> pairing code/setup URL
  -> REST + WebSocket protocol
  -> direct CLI playback
  -> streamed extension playback

Zam Reader bridge
  -> LocalTTSProvider
  -> LocalTTSBridge
  -> LocalhostTransport
  -> future NativeMessagingTransport seam
  -> provider registry integration
  -> Audio Panel status/CTA
  -> Options page full management
  -> contextual provider labels
  -> Web Speech fallback
  -> structured error/fallback handling

Testing
  -> helper unit tests
  -> engine adapter contract tests for Piper-plus + Kokoro
  -> catalog/model integrity tests
  -> REST contract tests
  -> WebSocket event-order tests
  -> security tests
  -> extension fake-helper tests
  -> real-helper integration smoke tests
  -> Firefox + Chromium e2e smoke tests
  -> manual QA checklist
```

**Implementation slicing rule:**

- Slices are allowed only as delivery sequencing.
- Slices must preserve the full architecture contracts from the beginning.
- No slice may hardcode a single engine, direct fetch from Reader UI, raw filesystem paths, unstructured errors, or provider-specific UI logic.

---

## Decision 22 — Development location

**Question:** Should the Local TTS Helper be developed in the Zam Reader repo, under a same-repo app subdirectory, or in a separate repository?

**Verdict:** Develop the helper in a **separate repository** from day one: `zam-local-tts-helper`.

**Rationale:**

- User explicitly chose separate repo to keep the helper clean from the beginning.
- The helper is a standalone app/package with its own Python runtime, model management, CLI, server, tests, packaging, and release lifecycle.
- Zam Reader is a strict WXT extension repo with TypeScript/WXT-specific boundaries, lint gates, and folder constraints.
- Keeping the helper separate preserves SoC and prevents Python/runtime packaging concerns from leaking into Zam Reader.
- Zam Reader should integrate only through the versioned bridge contract and fake/real helper tests.

**Repository split:**

```text
zaob-dev/
  zreader/                 # WXT browser extension
  zam-local-tts-helper/    # standalone Python helper app/package
```

**Zam Local TTS Helper owns:**

- Python package and CLI.
- REST/WebSocket API.
- Engine adapters for Piper-plus and Kokoro.
- Catalog/model management.
- Storage/cache/checksum/signature logic.
- Pairing/security.
- Helper diagnostics and logs.
- Helper CI and packaging.

**Zam Reader owns:**

- LocalTTSProvider.
- LocalTTSBridge client.
- LocalhostTransport and future NativeMessagingTransport seam.
- Audio Panel and Options UI.
- Web Speech fallback.
- Extension-side structured error handling.
- Fake-helper tests and real-helper smoke integration.

**Documentation implication:**

- Helper-specific design docs must be copied/moved into `zam-local-tts-helper/docs/`.
- Zam Reader may keep references or summaries, but the helper repo becomes the canonical home for helper architecture and readiness requirements.

---

## Open Decision Queue

The following branches still need grilling:

1. Final architecture synthesis / PRD handoff.
2. Issue breakdown for standalone helper app and Zam Reader bridge.
