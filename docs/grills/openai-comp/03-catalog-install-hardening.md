# Grill 03 — Catalog/install hardening

**Parent:** `docs/grills/openai-comp/02-streaming-design.md`  
**Status:** Q28–Q40 recommended; catalog/install hardening grill closed

This grill designs the next feature after:

1. P0 OpenAI-compatible blocking speech.
2. P1 raw PCM HTTP streaming.

The feature is **catalog/install hardening**: the native Mery infrastructure that makes many providers usable without turning the OpenAI-compatible route into provider-specific glue.

The standing constraints for every decision:

- Flexible: supports many engine/provider voice shapes without rewrites.
- Clean: avoids route-level/provider-level hacks.
- SoC: catalog, install, artifacts, voice registry, and API transport stay separate.
- Modular technically: new providers add catalog entries/adapters, not core rewrites.
- Standalone: install pipeline works independently of OpenAI compat.
- Scalable: safe for many voices, shared artifacts, remote catalogs, retries, and deletion.
- Well-tested: contract tests with fake catalog/install fixtures before real provider fixtures.

---

## Decision tree

- Q28 Catalog/install hardening scope: **full model/voice registry flywheel, tracer-bulleted**.
- Q29 Install API identity: **accept catalog-owned stable entry IDs, not URLs or raw installed voice IDs**.
- Q30 Catalog document shape: **normalized signed catalog internally, flat installable voice cards externally**.
- Q31 Catalog trust model: **two trust tiers — bundled trusted by package install, remote signed and freshness-checked**.
- Q32 Install job model: **always asynchronous, even for small bundled/fake installs**.
- Q33 Install job persistence: **durable local job store behind an `InstallJobStore` protocol, file-based first, SQLite later if needed**.
- Q34 Artifact storage identity: **catalog-defined artifact IDs separate from voice IDs, with voice manifests referencing artifacts and GC removing only unreferenced bytes**.
- Q35 Install atomicity: **installed voice manifest is the commit point; `VoiceRegistry` is runtime cache, not source of truth**.
- Q36 Delete semantics: **delete installed voices by `voiceId`; artifact garbage collection removes only unreferenced artifacts**.
- Q37 Registry refresh trigger: **application services call `VoiceRegistry.refresh()` after committed install/delete lifecycle changes; routes and stores do not**.
- Q38 Installed voice manifest payload: **persist logical artifact references and payload templates; hydrate concrete runtime paths during `VoiceRegistry.refresh()`**.
- Q39 First implementation slice: **one vertical fake-catalog tracer bullet that proves catalog -> install job -> artifacts -> voice manifest -> refresh -> delete/GC lifecycle before real downloads**.
- Q40 Definition of done: **fake lifecycle complete plus one real provider catalog entry validated; do not require all providers**.

---

## Q28 — Catalog/install hardening scope

### Recommendation

Choose **C: full model/voice registry flywheel**, but implement it with a narrow tracer bullet first.

The design target should be the complete native install pipeline:

```text
signed catalog
-> install job
-> allowlist/SHA/size verification
-> temp download
-> atomic artifact install
-> installed voice manifest
-> VoiceRegistry.refresh()
-> delete + unreferenced artifact GC
```

The first implementation slice should be intentionally small:

```text
bundled/signed catalog
-> one fake install job
-> one Piper/Kokoro-style catalog voice
-> verified artifact fixture
-> installed voice manifest
-> VoiceRegistry.refresh()
-> contract tests
```

### Why this is the right next feature

After OpenAI-compatible blocking speech and raw PCM streaming, Mery’s bottleneck is no longer “can an app call us?” The bottleneck becomes: **can users safely discover, install, trust, route, and remove voices across many providers without changing code?**

That makes catalog/install hardening the natural next Protocol-first feature. It converts the provider roadmap from a pile of engine candidates into a safe operational flywheel.

### Boundary

This feature is native Mery infrastructure, not OpenAI-specific infrastructure.

```text
/v1/audio/speech       -> consumes installed voices
/v1/voices/installed   -> lists local routable voices
/v1/catalog/voices     -> lists installable trusted voices
/v1/models/install     -> starts install job from catalog voice/model id
/v1/models/install/{id} -> reads install job status
DELETE /v1/models/{id} -> removes installed voice/model safely
/v1/events             -> streams install progress/events
```

OpenAI compat should never know download URLs, SHA256 hashes, catalog signatures, temp paths, artifact manifests, or garbage collection rules. It only resolves a requested voice to an installed `VoiceDescriptor` through `VoiceRegistry`.

### Clean architecture split

Recommended module boundaries:

```text
src/mery_tts/catalog/
  schemas.py          # CatalogVoiceEntry, CatalogFile, CatalogDocument
  signature.py        # Ed25519 verification and catalog trust policy
  repository.py       # bundled/remote catalog loading

src/mery_tts/install/
  jobs.py             # install job model, status, progress
  service.py          # install orchestration use case
  downloader.py       # allowlisted download into temp paths
  verifier.py         # sha256/size checks
  artifact_store.py   # atomic artifact writes + manifests
  voice_store.py      # installed voice manifests
  garbage.py          # unreferenced artifact cleanup

src/mery_tts/voices/
  registry.py         # installed voice routing, copy-on-write refresh

src/mery_tts/api/routes/
  catalog.py          # transport only: /v1/catalog/voices
  models.py           # transport only: install/status/delete endpoints
```

Dependency direction:

```text
API routes
-> install/catalog application services
-> catalog repository / artifact store / voice store
-> filesystem + HTTP adapters

OpenAI compat
-> VoiceRegistry only
```

### Scalable invariant

All providers, regardless of engine shape, should pass through the same install invariant:

```text
Catalog entry describes what may be installed.
Install service verifies bytes and writes manifests.
VoiceRegistry routes only installed manifests.
Adapters synthesize only from resolved VoiceDescriptor payloads.
```

This keeps 19+ providers manageable. Piper-style ONNX voices, Kokoro preset/shared artifacts, NeuTTS GGUF models, VoxCPM2 checkpoints, and future voice-cloning/reference artifacts differ in catalog metadata and payload kind, not in route behavior.

### Test strategy

Minimum test suite for the first tracer bullet:

```text
unit/catalog_schema_test.py
  - parses valid catalog voice entry
  - rejects missing file sha256/size
  - rejects unknown payload kind

unit/catalog_signature_test.py
  - accepts trusted bundled catalog policy
  - rejects invalid remote signature
  - rejects expired remote catalog when policy requires freshness

unit/install_verifier_test.py
  - sha256 pass/fail
  - size pass/fail
  - allowlist pass/fail

unit/artifact_store_test.py
  - writes temp then atomic move
  - never exposes partial artifact
  - cleans temp on failure

unit/voice_store_test.py
  - writes installed voice manifest
  - safe voice_id filename transform preserves canonical voice_id

contract/models_install_test.py
  - POST /v1/models/install starts job from catalog id
  - invalid catalog id returns native error
  - completed job creates installed voice manifest
  - VoiceRegistry.refresh sees installed voice

contract/catalog_routes_test.py
  - GET /v1/catalog/voices returns installable entries
  - GET /v1/voices/installed returns only installed/routable voices
```

Real provider tests stay optional/marked. The default CI path should use fake catalog entries and fake artifact bytes so catalog/install correctness does not depend on large model downloads.

### Definition of done for this feature family

Catalog/install hardening is complete when:

1. A signed or trusted catalog document can be loaded.
2. `/v1/catalog/voices` exposes installable entries without leaking unsafe URLs as install authority.
3. `/v1/models/install` accepts a catalog voice/model id, not an arbitrary URL.
4. Downloads are allowlisted and verified by SHA256 and size before install.
5. Files are written to temp paths and atomically moved into the artifact store.
6. Installed voice manifests are written separately from artifact manifests.
7. `VoiceRegistry.refresh()` picks up newly installed voices without restarting the server.
8. Delete removes voice manifests and garbage-collects unreferenced artifacts only.
9. All behavior has fake-fixture unit/contract coverage.

### Explicit non-goals for the first slice

Do not include these in the first tracer bullet:

- Every provider from the roadmap.
- Remote catalog refresh scheduling.
- Complex UI for install progress.
- Voice cloning consent workflows.
- GPU backend selection.
- Full storage dedupe across all model families.
- Automatic install when an OpenAI alias is missing.

Those are later slices. The first slice proves the invariant and the boundaries.

---

## Q29 — Catalog identity: what should `/v1/models/install` accept?

### Recommendation

Choose **C: accept a catalog-owned stable entry ID**, not a raw URL and not a raw installed `voice_id`.

Recommended request shape:

```json
POST /v1/models/install
{
  "catalogEntryId": "piper-plus:vi_VM_meeting-medium@2026-06-05"
}
```

The install API should treat `catalogEntryId` as the install authority. The install service resolves that ID through the trusted catalog, then reads the catalog entry to determine:

- resulting installed `voiceId`;
- `engineId`;
- payload kind;
- artifact files;
- SHA256 hashes;
- expected sizes;
- license/commercial-use metadata;
- source metadata;
- install policy.

### Why not raw URL?

Raw URL install looks flexible, but it breaks the security model.

If clients can send arbitrary URLs, they bypass:

- signed catalog trust;
- download allowlist;
- known file hashes;
- expected file sizes;
- license metadata;
- source provenance;
- future governance checks.

That turns `/v1/models/install` into a generic downloader. Mery should not do that.

### Why not raw `voice_id`?

A raw `voice_id` is the identity of an installed/routable voice. It should not be the authority for downloadable catalog content.

The distinction should stay clear:

```text
catalogEntryId -> installable trusted catalog item
voiceId        -> installed/routable voice identity
artifactId     -> stored bytes/model package identity
engineId       -> adapter/provider identity
```

A catalog entry may install one voice today, but future catalog entries may install:

- one shared artifact with many voices;
- one voice with multiple artifacts;
- a model family where voices are presets inside a shared file;
- a reference/designed voice that produces a new installed voice manifest;
- an updated version of an existing voice.

Using only `voice_id` makes those cases ambiguous too early.

### Recommended catalog schema identity fields

```python
class CatalogVoiceEntry(BaseModel):
    catalog_entry_id: str
    schema_version: Literal["1.0"]
    catalog_version: str

    voice_id: str
    engine_id: str
    display_name: str
    language: str
    locale: str | None = None
    quality_tier: Literal["low", "medium", "high"]

    payload_kind: Literal["preset", "model-file", "embedding", "reference", "designed"]
    artifact_ids: list[str]
    files: list[CatalogFile]

    license: str
    commercial_use: Literal["allowed", "restricted", "unknown"]
    source: CatalogSource
```

The ID should be stable enough for users/scripts, but version-aware enough to avoid ambiguous installs.

Recommended format:

```text
{engineId}:{providerVoiceSlug}@{catalogVersionOrRelease}
```

Examples:

```text
piper-plus:vi_VM_meeting-medium@2026-06-05
kokoro:af_bella@kokoro-v1
neutts-air:default-q4@2025-10
voxcpm2:vi-default@2026-04
```

### API boundary

`POST /v1/models/install` should not accept a URL.

It should accept:

```python
class InstallModelRequest(BaseModel):
    catalog_entry_id: str = Field(alias="catalogEntryId")
```

Optional future fields can be added without breaking the boundary:

```python
class InstallModelRequest(BaseModel):
    catalog_entry_id: str = Field(alias="catalogEntryId")
    preferred_backend: Literal["cpu", "coreml_ane", "cuda", "rocm"] | None = None
    force_reinstall: bool = False
```

But P0/P1 should keep the request minimal.

### Install flow

```text
POST /v1/models/install { catalogEntryId }
  -> CatalogRepository.get(catalogEntryId)
  -> verify catalog trust policy
  -> create install job
  -> InstallService downloads catalog-declared files only
  -> Downloader enforces allowlist
  -> Verifier enforces sha256 + size
  -> ArtifactStore writes temp then atomic move
  -> VoiceStore writes installed voice manifest
  -> VoiceRegistry.refresh()
  -> job completed
```

The request gives intent. The catalog supplies authority.

### Error behavior

Native Mery error examples:

```text
catalog.entry_not_found
catalog.untrusted
catalog.expired
install.already_installed
install.download_not_allowed
install.hash_mismatch
install.size_mismatch
install.unsupported_payload_kind
```

OpenAI compat should not translate these unless an OpenAI route indirectly triggers them later. For native install routes, native error shape is correct.

### Test strategy

Minimum tests for this decision:

```text
unit/install_request_schema_test.py
  - accepts catalogEntryId
  - rejects arbitrary url field
  - rejects raw voiceId-only request

unit/catalog_repository_test.py
  - resolves existing catalog_entry_id
  - returns entry_not_found for missing id
  - handles two catalog entries with same voice_id but different versions

contract/models_install_identity_test.py
  - POST /v1/models/install with catalogEntryId starts job
  - POST with url is rejected
  - POST with voiceId only is rejected
  - install job records catalog_entry_id and resulting voice_id separately
```

### Decision

Use `catalogEntryId` as the only install identity accepted by `/v1/models/install`.

This keeps the design flexible for many providers, clean in its boundaries, modular in implementation, standalone from OpenAI compatibility, scalable to versioned catalogs and shared artifacts, and well-tested through fake catalog fixtures.

---

## Q30 — Catalog document shape: flat `voices[]` or normalized graph?

### Recommendation

Use a **normalized catalog document internally**, but expose **flat installable voice cards externally**.

The signed catalog should be shaped like this:

```text
CatalogDocument
  engines[]
  artifacts[]
  voices[]
```

The public API should expose this:

```text
GET /v1/catalog/voices -> CatalogVoiceCard[]
```

This gives Mery the best of both worlds: the catalog remains scalable and deduplicated for many provider shapes, while clients still see a simple list of voices they can install.

### Why not flat-only?

A flat-only `voices[]` catalog is tempting because it is easy to read, but it breaks down as soon as providers stop being one-file-per-voice.

Provider examples:

```text
Piper-plus
  one voice -> one ONNX file + one config file

Kokoro
  many preset voices -> one shared model artifact + voice metadata/preset names

NeuTTS Air
  many voices/settings -> one GGUF model artifact + runtime voice config

VoxCPM2
  checkpoint/tokenizer/config artifacts -> multiple voices or voice-design presets

Future cloning engines
  base model artifact -> many user-created reference/designed voice manifests
```

If the signed catalog is only flat `voices[]`, shared model files get duplicated across entries. That makes storage planning, install idempotency, updates, deletion, and garbage collection harder than necessary.

### Recommended internal catalog schema

```python
class CatalogDocument(BaseModel):
    schema_version: Literal["1.0"]
    catalog_id: str
    catalog_version: str
    generated_at: datetime
    expires_at: datetime | None = None

    engines: list[CatalogEngine]
    artifacts: list[CatalogArtifact]
    voices: list[CatalogVoice]

    signature: CatalogSignature | None = None
```

```python
class CatalogEngine(BaseModel):
    engine_id: str
    display_name: str
    provider: str
    license: str
    homepage_url: str | None = None
    adapter_package: str | None = None
    min_adapter_version: str | None = None
    capabilities: EngineCapabilitySet
```

```python
class CatalogArtifact(BaseModel):
    artifact_id: str
    engine_id: str
    display_name: str
    artifact_type: Literal["model", "voice-pack", "tokenizer", "config", "embedding", "reference-audio"]
    files: list[CatalogFile]
    size_bytes: int
    license: str
    commercial_use: Literal["allowed", "restricted", "unknown"]
    source: CatalogSource
```

```python
class CatalogVoice(BaseModel):
    catalog_entry_id: str
    voice_id: str
    engine_id: str
    display_name: str
    language: str
    locale: str | None = None
    quality_tier: Literal["low", "medium", "high"]
    payload_kind: Literal["preset", "model-file", "embedding", "reference", "designed"]
    artifact_refs: list[str]
    payload_template: VoicePayloadUnion
    recommended_for: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
```

The catalog graph is still simple: voices reference artifacts by ID, and both reference engines by ID. Do not over-normalize beyond this for the first version.

### Recommended external API projection

Clients should not receive the full normalized graph from `/v1/catalog/voices` by default. They should receive flattened cards:

```python
class CatalogVoiceCard(BaseModel):
    catalog_entry_id: str = Field(alias="catalogEntryId")
    voice_id: str = Field(alias="voiceId")
    engine_id: str = Field(alias="engineId")
    display_name: str = Field(alias="displayName")
    language: str
    locale: str | None = None
    quality_tier: Literal["low", "medium", "high"] = Field(alias="qualityTier")
    license: str
    commercial_use: Literal["allowed", "restricted", "unknown"] = Field(alias="commercialUse")
    size_bytes: int = Field(alias="sizeBytes")
    installed: bool
    recommended_for: list[str] = Field(alias="recommendedFor")
    capabilities: list[str]
```

Projection rule:

```text
CatalogVoice
  + referenced CatalogArtifact summaries
  + CatalogEngine summary
  + installed-state lookup
  -> CatalogVoiceCard
```

This keeps UI/API consumers simple: they can show a voice list, badges, size, engine, install state, and install button without understanding artifact graphs.

### Service boundary

Recommended split:

```text
CatalogRepository
  loads and verifies CatalogDocument
  exposes normalized graph queries

CatalogQueryService
  projects normalized graph into CatalogVoiceCard[]
  joins installed state from VoiceStore

InstallService
  accepts catalogEntryId
  resolves CatalogVoice + referenced CatalogArtifacts
  installs artifacts and writes voice manifest
```

Dependency direction:

```text
API /v1/catalog/voices
  -> CatalogQueryService
  -> CatalogRepository + VoiceStore

API /v1/models/install
  -> InstallService
  -> CatalogRepository + Downloader + Verifier + ArtifactStore + VoiceStore + VoiceRegistry
```

OpenAI compat remains outside this graph and depends only on installed voices through `VoiceRegistry`.

### Why this is flexible and modular

This design supports multiple provider shapes without changing the public install API:

```text
Piper voice
  CatalogVoice -> one model artifact + config file

Kokoro preset
  CatalogVoice -> shared Kokoro model artifact + preset payload

NeuTTS GGUF
  CatalogVoice -> GGUF artifact + runtime payload

VoxCPM2
  CatalogVoice -> checkpoint/tokenizer/config artifacts

Future user-created clone
  InstalledVoiceManifest -> base artifact refs + user reference payload
```

The normalized catalog absorbs provider complexity. The API stays flat.

### Versioning and compatibility

The signed document gets a `schema_version` and `catalog_version`.

Rules:

```text
schema_version -> parser compatibility
catalog_version -> catalog content/version identity
catalog_entry_id -> installable entry identity, version-aware
artifact_id -> stored artifact identity, stable across voices when shared
voice_id -> installed/routable voice identity
```

If `schema_version` is unsupported, reject the catalog before exposing entries. If `catalog_version` changes, already-installed manifests keep their source catalog metadata for provenance but remain installed unless explicitly removed or migrated.

### Test strategy

Minimum tests for this decision:

```text
unit/catalog_document_schema_test.py
  - parses engines/artifacts/voices graph
  - rejects voice referencing missing artifact
  - rejects artifact referencing missing engine
  - rejects duplicate catalog_entry_id
  - rejects duplicate artifact_id

unit/catalog_projection_test.py
  - projects normalized graph into flat CatalogVoiceCard
  - sums or reports artifact size correctly
  - includes installed=false for missing local voice
  - includes installed=true when VoiceStore has matching voice_id
  - hides raw download URLs from public voice cards

unit/install_graph_resolution_test.py
  - resolves catalogEntryId to voice + artifacts
  - handles one voice -> one artifact
  - handles many voices -> one shared artifact
  - handles one voice -> many artifacts

contract/catalog_voices_route_test.py
  - GET /v1/catalog/voices returns flat cards
  - response contains catalogEntryId and voiceId separately
  - response does not expose arbitrary install URL authority
```

### Decision

Use a normalized signed catalog internally:

```text
engines[] + artifacts[] + voices[]
```

Expose a flat external API:

```text
GET /v1/catalog/voices -> CatalogVoiceCard[]
```

This is the cleanest long-term boundary: scalable storage and install semantics inside, simple voice discovery outside.

---

## Q31 — Catalog trust model: bundled vs remote

### Recommendation

Use **two catalog trust tiers**:

```text
Bundled catalog
  -> trusted by package install
  -> schema-validated
  -> no network freshness requirement
  -> no mandatory runtime signature check

Remote catalog
  -> Ed25519 signature required
  -> schema-validated
  -> expiry/freshness checked
  -> source allowlist enforced
  -> reject closed on invalid trust
```

This follows ADR-0007’s existing direction: bundled catalog is trusted because it ships with the package; remote catalog is untrusted network data and must prove integrity before Mery exposes or installs anything from it.

### Why this split is correct

Bundled and remote catalogs have different threat models.

A bundled catalog is already part of the installed Mery package. If an attacker can modify package files on disk, they can likely modify runtime code too. Runtime signature checks for bundled data add boot complexity without materially improving the local compromise story.

A remote catalog is different. It crosses the network and may be cached, mirrored, or fetched from infrastructure that can fail independently. It must be verified before use.

The clean rule is:

```text
Bundled catalog trust comes from package distribution.
Remote catalog trust comes from signature + freshness + allowed source.
```

### Trust policy boundary

Do not scatter trust checks across routes, installers, or adapters. Put trust decisions behind one policy boundary:

```text
CatalogRepository
  -> loads raw catalog document
  -> calls CatalogTrustPolicy
  -> returns TrustedCatalogDocument only on success

CatalogQueryService
  -> accepts TrustedCatalogDocument only

InstallService
  -> accepts TrustedCatalogDocument only
```

Recommended types:

```python
class CatalogSourceKind(StrEnum):
    BUNDLED = "bundled"
    REMOTE = "remote"

class CatalogTrustDecision(BaseModel):
    trusted: bool
    source_kind: CatalogSourceKind
    catalog_id: str
    catalog_version: str
    reason: str | None = None

class TrustedCatalogDocument(BaseModel):
    document: CatalogDocument
    trust: CatalogTrustDecision
```

The important design point: once code receives `TrustedCatalogDocument`, it should not repeat signature logic. That keeps SoC tight.

### Bundled catalog rules

Bundled catalog validation should include:

```text
- parse JSON
- validate schema_version compatibility
- validate graph references
- validate duplicate IDs absent
- validate required hashes/sizes/allowlisted source metadata exist
```

Bundled catalog validation should not require:

```text
- network freshness
- remote expiry freshness
- runtime Ed25519 signature
```

A bundled catalog may still include a signature for provenance, but runtime should not depend on it for boot.

### Remote catalog rules

Remote catalog validation should include:

```text
- fetch from configured catalog URL only
- verify URL/source against catalog source allowlist
- verify Ed25519 signature over canonical catalog bytes
- validate schema_version compatibility
- validate generated_at/expires_at freshness
- validate graph references
- validate duplicate IDs absent
- validate every file has sha256 + sizeBytes
- reject closed if any required trust check fails
```

Remote catalog failure should not break already-installed voices. It should only prevent exposing new remote installable entries from that failed catalog.

### Signature boundary

Recommended module:

```text
src/mery_tts/catalog/signature.py
```

Responsibilities:

```text
- canonicalize bytes or verify detached signature format
- verify Ed25519 signature with configured public keys
- return structured errors, not booleans
```

Do not mix signature verification with install download verification. They are different layers:

```text
Catalog signature -> proves metadata document integrity
File SHA256       -> proves downloaded artifact integrity
```

Both are required for remote installs.

### Failure behavior

Recommended native errors:

```text
catalog.schema_unsupported
catalog.schema_invalid
catalog.graph_invalid
catalog.duplicate_id
catalog.remote_not_allowed
catalog.signature_missing
catalog.signature_invalid
catalog.expired
catalog.untrusted
```

Behavior:

```text
GET /v1/catalog/voices
  bundled trust failure -> 500 or degraded diagnostics, because packaged data is broken
  remote trust failure  -> omit remote entries + report diagnostics, because installed voices can still run

POST /v1/models/install
  catalogEntryId from untrusted/missing catalog -> 404 or catalog.untrusted depending whether entry was visible before
```

Do not silently install from an untrusted catalog. Failure must be explicit.

### Config shape

Recommended settings:

```python
class CatalogSettings(BaseModel):
    bundled_catalog_enabled: bool = True
    remote_catalog_enabled: bool = False
    remote_catalog_url: AnyUrl | None = None
    trusted_public_keys: list[str] = Field(default_factory=list)
    max_catalog_age_seconds: int = 7 * 24 * 3600
    allowed_download_hosts: list[str] = Field(default_factory=list)
```

Remote catalog should be opt-in until the project has production signing/release infrastructure. Bundled catalog can ship first.

### Test strategy

Minimum tests for this decision:

```text
unit/catalog_trust_policy_test.py
  - bundled valid schema returns TrustedCatalogDocument
  - bundled invalid schema fails
  - bundled does not require signature
  - remote valid signature + fresh expiry returns TrustedCatalogDocument
  - remote missing signature fails
  - remote invalid signature fails
  - remote expired catalog fails
  - remote unsupported schema fails

unit/catalog_signature_test.py
  - verifies canonical signed payload
  - rejects modified payload
  - rejects unknown key id
  - rejects malformed signature

contract/catalog_route_trust_test.py
  - GET /v1/catalog/voices exposes bundled trusted entries
  - remote trust failure does not expose remote entries
  - diagnostics report remote catalog trust failure

contract/install_trust_test.py
  - POST /v1/models/install cannot install entry from untrusted remote catalog
  - install job records catalog trust/source metadata for successful install
```

### Decision

Use two trust tiers:

```text
Bundled catalog -> trusted by package install + schema/graph validation
Remote catalog  -> Ed25519 signature + freshness + source allowlist + schema/graph validation
```

This keeps the system flexible and standalone for offline installs, clean in trust boundaries, modular in implementation, scalable to remote catalog distribution, and well-tested without depending on real network services.

---

## Q32 — Install job model: sync install or async job?

### Recommendation

Use **async install jobs always**, even for small bundled or fake installs.

Recommended contract:

```text
POST /v1/models/install
  -> 202 Accepted
  -> { jobId, status: "queued" }

GET /v1/models/install/{jobId}
  -> current job status/progress/result/error

/v1/events
  -> optional install progress events
```

Do not make small installs synchronous and large installs asynchronous. That creates two API semantics for the same operation and makes clients harder to write.

### Why async always

Real installs are naturally asynchronous:

```text
resolve catalog entry
-> download one or more files
-> verify allowlist/SHA256/size
-> write temp files
-> atomically move artifacts
-> write manifests
-> refresh VoiceRegistry
-> emit events
```

Even a “small” install can fail, take time, or need cancellation. Async jobs keep the API stable from fake test fixtures to multi-GB model packages.

The client contract stays simple:

```text
start job once
poll status or subscribe to events
use installed voice after completed
```

### Job state machine

Recommended state machine:

```text
queued
  -> resolving
  -> downloading
  -> verifying
  -> installing
  -> refreshing
  -> completed

queued/resolving/downloading/verifying/installing/refreshing
  -> failed
  -> cancelled
```

Recommended enum:

```python
class InstallJobStatus(StrEnum):
    QUEUED = "queued"
    RESOLVING = "resolving"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    INSTALLING = "installing"
    REFRESHING = "refreshing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

### Job schema

```python
class InstallJob(BaseModel):
    job_id: str
    status: InstallJobStatus
    catalog_entry_id: str
    catalog_version: str | None = None
    voice_id: str | None = None
    engine_id: str | None = None

    progress: InstallProgress
    result: InstallResult | None = None
    error: InstallError | None = None

    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
```

```python
class InstallProgress(BaseModel):
    phase: InstallJobStatus
    message: str
    bytes_downloaded: int = 0
    bytes_total: int | None = None
    files_completed: int = 0
    files_total: int | None = None
```

```python
class InstallResult(BaseModel):
    voice_id: str
    engine_id: str
    artifact_ids: list[str]
    installed_voice_manifest_path: str | None = None
```

Do not expose local filesystem paths in public API by default. If paths are needed for diagnostics, expose them only under diagnostics/debug endpoints.

### Service boundary

Recommended split:

```text
API route
  -> validates InstallModelRequest
  -> calls InstallJobService.enqueue(catalogEntryId)
  -> returns 202 + job id

InstallJobService
  -> creates and stores job
  -> schedules runner
  -> owns job status transitions

InstallRunner
  -> calls InstallService
  -> catches domain errors
  -> updates job state

InstallService
  -> resolves catalog entry
  -> downloads/verifies/artifact writes/voice manifest/refresh
```

This keeps route code tiny and lets tests drive the runner synchronously without changing the public API.

### Event boundary

`/v1/events` should observe install jobs; it should not own install state.

Recommended event shape:

```python
class InstallJobEvent(BaseModel):
    type: Literal["install.job.updated"]
    job_id: str
    status: InstallJobStatus
    catalog_entry_id: str
    voice_id: str | None = None
    progress: InstallProgress
    error: InstallError | None = None
```

Event delivery is best-effort. Job state is authoritative in `InstallJobStore`, not in the event stream.

### Cancellation

Even if cancellation is not exposed in the first route slice, the job model should allow it.

Future endpoint:

```text
DELETE /v1/models/install/{jobId}
  -> request cancellation
```

Cancellation behavior:

```text
queued -> cancelled immediately
resolving/downloading/verifying/installing -> cancellation requested cooperatively
refreshing -> may finish if atomic commit already happened
completed/failed/cancelled -> idempotent no-op or 409 depending API preference
```

The first implementation can omit the cancellation endpoint but should not design a state model that makes cancellation impossible.

### Idempotency and duplicates

The job layer should prevent duplicate installs from corrupting state.

Recommended initial behavior:

```text
If voice already installed:
  return 200/202 with completed job-like response or new job that immediately completes.

If same catalogEntryId currently installing:
  return existing in-progress job instead of starting a duplicate.

If forceReinstall=true later:
  create explicit reinstall job.
```

For the first slice, simplest clean rule:

```text
catalogEntryId + status in active states must be unique.
```

Active states:

```text
queued, resolving, downloading, verifying, installing, refreshing
```

### Test strategy

Minimum tests for this decision:

```text
unit/install_job_state_test.py
  - valid state transitions pass
  - invalid transitions fail
  - completed/failed/cancelled are terminal

unit/install_job_service_test.py
  - enqueue creates queued job
  - duplicate active catalogEntryId returns existing active job
  - already installed voice returns completed result or immediate-complete job

unit/install_runner_test.py
  - successful fake install transitions through resolving/downloading/verifying/installing/refreshing/completed
  - domain error transitions to failed with structured error
  - runner updates progress

contract/models_install_async_test.py
  - POST /v1/models/install returns 202 and jobId
  - GET /v1/models/install/{jobId} returns status
  - completed job includes voiceId and engineId
  - failed job includes structured error

contract/install_events_test.py
  - install job emits progress events when event bus is enabled
  - job state remains queryable even if no event subscriber exists
```

### Decision

Use async install jobs for every install.

This keeps the install feature flexible across small and huge providers, cleanly separated from transport, modular in runner/service/store responsibilities, standalone from OpenAI compatibility, scalable to progress/cancellation/retry, and well-tested with deterministic fake job runners.

---

## Q33 — Install job persistence: memory-only or durable local store?

### Recommendation

Use a **durable local job store** behind an `InstallJobStore` protocol. Start with a simple file-based implementation, and leave room for SQLite later if install history/querying grows.

Do not make production install jobs memory-only.

Recommended first backend:

```text
{app_data_dir}/install/jobs/{jobId}.json
```

Future backend if needed:

```text
SQLiteInstallJobStore
```

The API and install services should depend on the protocol, not the concrete backend.

### Why durable jobs are necessary

Install jobs are not like short request-local calculations. They can involve:

```text
large downloads
slow network
multi-file verification
filesystem writes
server restart
user troubleshooting
progress polling
future cancellation/retry
```

If jobs are memory-only, then a server restart loses:

- job status;
- failure reason;
- progress;
- mapping from `catalogEntryId` to active/completed job;
- evidence of whether an install completed or failed halfway.

That makes install behavior brittle exactly where users need it to be reliable.

### Clean abstraction

Define a narrow persistence boundary:

```python
class InstallJobStore(Protocol):
    async def create(self, job: InstallJob) -> None: ...
    async def get(self, job_id: str) -> InstallJob | None: ...
    async def find_active_by_catalog_entry(self, catalog_entry_id: str) -> InstallJob | None: ...
    async def update(self, job: InstallJob) -> None: ...
    async def list_recent(self, limit: int = 50) -> list[InstallJob]: ...
```

The job store owns persistence. It should not own install logic, downloads, verification, artifact writes, or registry refresh.

Boundary:

```text
InstallJobService -> InstallJobStore
InstallRunner     -> InstallJobStore
API routes        -> InstallJobService, not raw store where possible
```

### File-based first backend

A file-based store is enough for the first production-quality slice if it is implemented carefully.

Recommended layout:

```text
{app_data_dir}/install/
  jobs/
    {jobId}.json
  locks/
    {catalogEntryIdHash}.lock   # optional future guard
```

Write policy:

```text
write job JSON to temp file
fsync temp file when practical
atomic rename to {jobId}.json
never leave partial job JSON as canonical state
```

This mirrors the artifact install principle: temp first, atomic commit second.

### Restart behavior

On startup, the job service should reconcile unfinished jobs.

Recommended first behavior:

```text
queued/running job from previous process
  -> mark failed with reason install.interrupted
  -> do not auto-resume downloads in first slice

completed/failed/cancelled job
  -> keep as history
```

Why not auto-resume first? Resume requires byte-range support, partial file validation, and more complicated temp cleanup. That is a later feature. The clean MVP is honest: interrupted jobs fail explicitly and can be retried.

### Duplicate active job handling

Durable store helps enforce idempotency:

```text
find_active_by_catalog_entry(catalogEntryId)
  -> if active job exists, return it instead of creating another
  -> if no active job exists, create new queued job
```

Active statuses:

```text
queued, resolving, downloading, verifying, installing, refreshing
```

Terminal statuses:

```text
completed, failed, cancelled
```

### Why not SQLite first?

SQLite is a good future backend, but file-based storage is enough at first because:

- job volume is low;
- access patterns are simple;
- each job is naturally one document;
- tests are simpler with temp directories;
- no migration story is needed yet.

The important part is not the backend. The important part is the `InstallJobStore` protocol so the backend can change without touching API routes or install orchestration.

### Test strategy

Minimum tests for this decision:

```text
unit/install_job_store_protocol_test.py
  - shared behavior contract for fake and file stores
  - create/get roundtrip
  - update persists status/progress/error/result
  - list_recent sorts by updated_at or created_at
  - find_active_by_catalog_entry ignores terminal jobs

unit/file_install_job_store_test.py
  - writes job JSON atomically
  - recovers valid job after process-style reload
  - ignores or reports malformed job JSON safely
  - temp write failure does not corrupt existing job

unit/install_startup_reconcile_test.py
  - previous queued/running jobs become failed install.interrupted
  - terminal jobs remain unchanged

contract/models_install_persistence_test.py
  - POST creates durable job
  - GET can read job after service/store reinitialization
  - duplicate active install returns existing active job
```

### Decision

Use a durable local `InstallJobStore` protocol with a file-based backend first:

```text
{app_data_dir}/install/jobs/{jobId}.json
```

Keep in-memory store only for tests. Add SQLite later only if query complexity or packaging needs justify it.

This keeps install jobs standalone and reliable, preserves clean SoC, supports scalable future persistence backends, and remains well-tested with both fake and temp-dir stores.

---

## Q34 — Artifact storage identity: how should installed bytes be named and deduped?

### Recommendation

Use **catalog-defined artifact IDs separate from voice IDs**, verified by SHA256, with manifest-owned file paths.

Do not use `voice_id` as the storage folder.

Recommended layout:

```text
{app_data_dir}/
  artifacts/
    {engineId}/
      {artifactId}/
        artifact.json
        files/
          model.onnx
          config.json
          tokenizer.json
  voices/
    {safeVoiceId}.json
```

Identity split:

```text
artifactId -> stored package/bytes identity
voiceId    -> routable installed voice identity
engineId   -> adapter identity
```

The core rule:

```text
Voice manifests reference artifacts.
Artifacts do not belong to one voice.
```

### Why not store by voice ID?

Storing bytes under `voice_id` works only for the simplest provider shape:

```text
one voice -> one model file
```

But Mery’s roadmap already includes more shapes:

```text
Kokoro
  many preset voices -> one shared model artifact

Piper-plus
  one voice -> model + config artifact package

VoxCPM2
  one voice/design path -> checkpoint + tokenizer + config artifacts

NeuTTS Air
  many runtime voices/settings -> one GGUF artifact

Future cloning
  one base model artifact -> many user-created reference/designed voices
```

If storage is keyed by `voice_id`, deletion and dedupe become dangerous:

- deleting one Kokoro voice might delete bytes needed by other Kokoro voices;
- reinstalling the same shared model duplicates bytes;
- one voice with multiple artifacts becomes awkward;
- artifact provenance is mixed with voice routing identity.

Separate artifact identity avoids that.

### Artifact ID source

`artifactId` should come from the trusted catalog, not from user input.

Recommended examples:

```text
piper-plus-vi_VM_meeting-medium-onnx-2026-06
kokoro-v1-onnx
neutts-air-q4-gguf-2025-10
voxcpm2-base-2b-2026-04
```

The artifact ID should be stable across catalog versions when bytes are the same, and change when bytes change.

The actual file integrity still comes from SHA256 per file:

```text
artifactId names the package.
file.sha256 verifies the bytes.
```

Do not treat a pretty artifact ID as a cryptographic guarantee.

### Artifact manifest

Recommended installed artifact manifest:

```python
class InstalledArtifactManifest(BaseModel):
    schema_version: Literal["1.0"]
    artifact_id: str
    engine_id: str
    artifact_type: Literal["model", "voice-pack", "tokenizer", "config", "embedding", "reference-audio"]

    source_catalog_id: str | None = None
    source_catalog_version: str | None = None
    source_catalog_entry_ids: list[str] = Field(default_factory=list)

    license: str
    commercial_use: Literal["allowed", "restricted", "unknown"]
    files: list[InstalledArtifactFile]

    installed_at: datetime
    verified_at: datetime
```

```python
class InstalledArtifactFile(BaseModel):
    file_role: Literal["model", "config", "tokenizer", "weights", "metadata", "voice-pack"]
    relative_path: str
    sha256: str
    size_bytes: int
```

The manifest is the only source of truth for local file paths. Code should not infer paths from provider conventions unless an adapter explicitly interprets a voice payload after registry resolution.

### Voice manifest references

Installed voice manifests should reference artifacts by ID:

```python
class InstalledVoiceManifest(BaseModel):
    schema_version: Literal["1.0"]
    voice_id: str
    engine_id: str
    display_name: str
    language: str
    quality_tier: Literal["low", "medium", "high"]

    source_catalog_entry_id: str | None = None
    artifact_refs: list[str]
    payload: VoicePayloadUnion

    installed_at: datetime
```

Example Kokoro:

```json
{
  "voiceId": "kokoro:af_bella",
  "engineId": "kokoro",
  "artifactRefs": ["kokoro-v1-onnx"],
  "payload": {
    "kind": "preset",
    "presetName": "af_bella"
  }
}
```

Example Piper-plus:

```json
{
  "voiceId": "piper-plus:vi_VM_meeting-medium",
  "engineId": "piper-plus",
  "artifactRefs": ["piper-plus-vi_VM_meeting-medium-onnx-2026-06"],
  "payload": {
    "kind": "model-file",
    "modelPath": "...resolved from artifact manifest...",
    "configPath": "...resolved from artifact manifest..."
  }
}
```

Implementation note: the persisted payload may store logical file roles or relative paths, and `VoiceRegistry` can hydrate runtime absolute paths from `ArtifactStore`. Avoid storing brittle absolute paths when possible.

### Install behavior

Install service flow:

```text
CatalogVoice.artifact_refs
  -> resolve CatalogArtifact nodes
  -> for each artifact:
       if already installed and files verify, reuse
       else download to temp
       verify sha256 + size
       atomic move into artifacts/{engineId}/{artifactId}
       write artifact.json
  -> write voice manifest referencing artifact IDs
  -> VoiceRegistry.refresh()
```

This allows one artifact install to unlock multiple voices later without redownloading.

### Delete and garbage collection

Delete should operate on installed voice identity first:

```text
DELETE /v1/models/{voiceId}
  -> remove voice manifest
  -> compute artifact reference counts
  -> remove artifacts with zero references only
  -> VoiceRegistry.refresh()
```

Do not delete artifacts blindly based on the deleted voice’s folder. There should be no such coupling.

Reference count source:

```text
all InstalledVoiceManifest.artifact_refs
```

If an artifact is unreferenced but deletion fails, report diagnostics and leave the system in a safe state. Orphaned bytes are annoying; missing bytes for an installed voice are worse.

### Test strategy

Minimum tests for this decision:

```text
unit/artifact_store_test.py
  - installs artifact under engineId/artifactId
  - writes artifact manifest atomically
  - verifies existing artifact files before reuse
  - rejects existing artifact with hash mismatch
  - does not infer paths from voice_id

unit/voice_manifest_test.py
  - voice manifest references artifact IDs
  - safe voice filename preserves canonical voice_id
  - VoiceRegistry can hydrate runtime descriptor from artifact refs

unit/artifact_gc_test.py
  - deleting one of two voices sharing artifact keeps artifact
  - deleting last referencing voice removes artifact
  - GC ignores malformed/unreadable voice manifest safely and reports diagnostic
  - failed artifact delete does not remove voice manifest unless operation order is explicit and tested

contract/install_shared_artifact_test.py
  - installing two voices with same artifact downloads artifact once
  - second install reuses verified artifact
  - both voices become routable after refresh
```

### Decision

Use catalog-defined `artifactId` for stored bytes and `voiceId` for routable voices.

```text
artifacts/{engineId}/{artifactId}/...
voices/{safeVoiceId}.json
```

Voice manifests reference artifacts, and garbage collection removes only unreferenced artifacts.

This keeps storage flexible across provider shapes, cleanly separates bytes from routing, modularizes artifact/voice lifecycle, stays standalone from OpenAI compatibility, scales to shared artifacts and multi-artifact voices, and is testable with fake artifact graphs.

---

## Q35 — Install atomicity: what is the commit point?

### Recommendation

The install commit point should be **writing the installed voice manifest atomically**.

Do not treat download completion, artifact file movement, or `VoiceRegistry.refresh()` as the install commit point.

Safe install order:

```text
1. resolve trusted catalog entry
2. download into job temp directory
3. verify SHA256 and size
4. atomically move/write artifact files and artifact manifests
5. atomically write installed voice manifest
6. call VoiceRegistry.refresh()
```

Before step 5, the voice must not appear installed. After step 5, the voice is installed from the storage layer’s point of view, even if `VoiceRegistry.refresh()` fails and needs retry/reconciliation.

### Why the voice manifest is the right commit point

Mery needs one durable authority for “is this voice installed?” That authority should be the installed voice manifest, not the presence of model bytes and not an in-memory registry cache.

Clean ownership:

```text
ArtifactStore
  -> owns installed bytes and artifact manifests

VoiceStore
  -> owns installed voice manifests
  -> source of truth for installed/routable voice inventory

VoiceRegistry
  -> runtime routing cache hydrated from VoiceStore + ArtifactStore
  -> not source of truth
```

This makes failure handling much cleaner.

### Failure semantics by phase

```text
Failure before artifact commit
  -> delete job temp directory
  -> no installed artifact
  -> no installed voice
  -> job failed

Failure after artifact commit but before voice manifest
  -> artifact may remain installed/reusable
  -> no installed voice
  -> artifact is orphan candidate or reusable for retry
  -> job failed

Failure after voice manifest but before refresh success
  -> voice is installed in durable storage
  -> runtime registry may not see it yet
  -> job can be marked failed_refresh or completed_with_warning
  -> startup/retry can refresh registry later

Failure after refresh
  -> job completed
  -> voice installed and routable
```

The key invariant:

```text
A voice is installed if and only if its installed voice manifest exists and validates.
```

### Why not artifact commit?

Artifact files alone do not tell Mery which voices should be routable.

For example:

```text
Kokoro artifact installed
  -> may support many preset voices
  -> not all presets should necessarily be exposed as installed voices

Base cloning model installed
  -> does not imply any user-created reference voice exists
```

So artifact commit means “bytes are available,” not “voice is installed.”

### Why not registry refresh?

`VoiceRegistry` is runtime state. It should be rebuildable.

If refresh is the commit point, a transient runtime failure can leave durable storage in an ambiguous state. Instead, manifest write commits durable intent, and registry refresh catches up.

Recommended startup behavior:

```text
server startup
  -> VoiceRegistry.refresh()
  -> validate installed voice manifests
  -> validate referenced artifacts exist and pass lightweight checks
  -> expose only valid voices
  -> report diagnostics for broken manifests/artifacts
```

### Atomic write policy

Voice manifest writes should follow temp-then-rename:

```text
voices/{safeVoiceId}.json.tmp-{jobId}
  -> fsync/write complete
  -> atomic rename to voices/{safeVoiceId}.json
```

Artifact manifests should use the same pattern:

```text
artifacts/{engineId}/{artifactId}/artifact.json.tmp-{jobId}
  -> atomic rename to artifact.json
```

No canonical manifest path should ever contain partial JSON.

### Job status recommendation

Use explicit status/error detail for refresh failures.

Option 1, stricter:

```text
refresh fails after voice manifest write
  -> job status = failed
  -> error code = install.refresh_failed_after_commit
  -> installed voice remains durable
  -> diagnostics instruct retry refresh/restart
```

Option 2, more user-friendly:

```text
refresh fails after voice manifest write
  -> job status = completed
  -> warning = voice_registry.refresh_failed
  -> diagnostics indicate runtime cache stale
```

Recommendation: start with **Option 1** because it is more honest for API clients. The voice is durably installed, but the install job did not achieve its user-visible goal: routability without restart. Startup reconciliation can later make it routable.

### Reconciliation

Add reconciliation as a service concern, not route logic:

```text
InstallReconciler
  -> scans artifacts and voice manifests
  -> finds orphan artifacts
  -> finds voice manifests with missing/bad artifact refs
  -> asks VoiceRegistry.refresh()
  -> reports diagnostics
```

First slice can implement only startup registry refresh and basic diagnostics. Full orphan cleanup can wait for delete/GC slice.

### Test strategy

Minimum tests for this decision:

```text
unit/install_atomicity_test.py
  - failure during download leaves no artifact and no voice manifest
  - failure during verification leaves no artifact and no voice manifest
  - failure after artifact commit leaves artifact but no voice manifest
  - failure after voice manifest commit leaves voice manifest present
  - canonical manifests are never partial JSON after simulated write failure

unit/voice_store_atomic_write_test.py
  - writes manifest via temp then atomic rename
  - existing manifest is not corrupted if replacement write fails
  - safe voice filename maps back to canonical voice_id

unit/voice_registry_refresh_boundary_test.py
  - VoiceRegistry hydrates from VoiceStore, not job state
  - refresh failure does not delete installed manifest
  - later refresh can make committed voice routable

contract/install_commit_point_test.py
  - completed install creates voice manifest before voice appears in /v1/voices/installed
  - forced refresh failure returns structured job error
  - after service restart/refresh, committed voice becomes visible
```

### Decision

The installed voice manifest is the install commit point.

```text
artifact exists without voice manifest -> reusable/orphan artifact
voice manifest exists and validates     -> voice is installed
VoiceRegistry contains voice            -> voice is currently routable in runtime cache
```

This keeps install semantics flexible across provider shapes, cleanly separates storage authority from runtime cache, modularizes failure recovery, stays standalone from OpenAI compatibility, scales to retries/reconciliation, and is well-tested through fault-injection around every install phase.

---

## Q36 — Delete semantics: delete by `voiceId`, `catalogEntryId`, or `artifactId`?

### Recommendation

Delete installed voices by **`voiceId` first**, and let artifact garbage collection remove only unreferenced bytes.

Recommended primary contract:

```text
DELETE /v1/models/{voiceId}
```

Meaning:

```text
remove installed voice manifest
-> refresh VoiceRegistry
-> compute artifact reference counts
-> garbage-collect artifacts with zero remaining voice references
```

Do not make `artifactId` or `catalogEntryId` the primary delete identity.

### Identity ownership

Each ID has a different lifecycle role:

```text
catalogEntryId -> installable catalog item identity
voiceId        -> installed/routable voice identity
artifactId     -> stored bytes/package identity
engineId       -> adapter identity
```

Delete is part of the installed lifecycle, so the user-facing delete operation should target `voiceId`.

### Why not delete by catalogEntryId?

`catalogEntryId` belongs to catalog/install authority, not installed runtime identity.

It has awkward edge cases:

- the same `voiceId` may be installed from a newer catalog entry later;
- a catalog entry may disappear from a remote catalog while the voice remains installed locally;
- installed manifests should remain usable even if catalog metadata changes;
- future user-created voices may not have a catalog entry at all.

So `catalogEntryId` is useful for provenance, but it should not be the main deletion handle.

### Why not delete by artifactId?

`artifactId` is storage-internal. Deleting it directly can break voices that reference it.

Examples:

```text
Kokoro artifact -> many installed preset voices
NeuTTS GGUF artifact -> many runtime voice configurations
Future cloning base model -> many reference/designed voices
```

If users delete an artifact directly, Mery must either reject the operation or cascade-delete voices. Both are more dangerous than deleting a voice first and letting GC decide whether bytes are still needed.

Optional later admin endpoint:

```text
DELETE /v1/artifacts/{artifactId}
```

But that should be diagnostics/admin-only and guarded by reference checks.

### Delete flow

Recommended flow:

```text
DELETE /v1/models/{voiceId}
  -> VoiceStore.get(voiceId)
  -> if missing: return idempotent success or model.not_installed
  -> remove voice manifest atomically
  -> VoiceRegistry.refresh()
  -> ArtifactGarbageCollector.collect_unreferenced()
  -> return deleted voice + removed artifact ids + retained artifact ids
```

Recommended response:

```python
class DeleteModelResponse(BaseModel):
    voice_id: str = Field(alias="voiceId")
    deleted: bool
    removed_artifact_ids: list[str] = Field(default_factory=list, alias="removedArtifactIds")
    retained_artifact_ids: list[str] = Field(default_factory=list, alias="retainedArtifactIds")
    warnings: list[str] = Field(default_factory=list)
```

### Idempotency recommendation

Make delete idempotent by default.

```text
DELETE missing voiceId -> 200/204 with deleted=false
```

Why: idempotent delete is easier for clients, retries, cleanup scripts, and uninstall flows. If strictness is needed later, add a query flag or diagnostic mode, not the default path.

### Atomicity and failure handling

Delete has two phases:

```text
Phase 1: remove installed voice manifest
Phase 2: refresh runtime registry and collect unreferenced artifacts
```

The voice manifest removal is the durable delete commit point.

Failure semantics:

```text
Failure before voice manifest removal
  -> voice remains installed
  -> no artifact GC

Failure after voice manifest removal but before refresh
  -> voice is durably deleted
  -> runtime registry may be stale until next refresh
  -> report delete.refresh_failed_after_commit

Failure during artifact GC
  -> voice remains deleted
  -> orphan artifact may remain
  -> report warning, not fatal voice delete failure
```

This mirrors install atomicity: manifests are storage authority; registry is runtime cache; GC is cleanup.

### Artifact garbage collection

GC should compute references from all valid installed voice manifests:

```text
all_voice_refs = union(voice_manifest.artifact_refs for every installed voice)
for artifact in ArtifactStore.list():
  if artifact.artifact_id not in all_voice_refs:
    remove artifact
```

Safety rule:

```text
If reference counting is uncertain, keep the artifact.
```

Disk leaks are recoverable. Breaking installed voices is worse.

### Service boundary

Recommended split:

```text
API route
  -> DeleteModelService.delete_voice(voiceId)

DeleteModelService
  -> VoiceStore removes voice manifest
  -> VoiceRegistry refreshes runtime cache
  -> ArtifactGarbageCollector removes unreferenced artifacts

ArtifactGarbageCollector
  -> reads VoiceStore + ArtifactStore
  -> never reads API request state directly
```

OpenAI compat should not participate in deletion. If an OpenAI alias points to a deleted voice, the normal alias/voice resolution path returns `voice_not_found` or an install hint.

### Test strategy

Minimum tests for this decision:

```text
unit/delete_model_service_test.py
  - deleting installed voice removes voice manifest
  - deleting missing voice is idempotent
  - refresh is called after delete
  - refresh failure after manifest removal returns structured warning/error

unit/artifact_gc_reference_test.py
  - shared artifact retained when another voice references it
  - artifact removed after last referencing voice is deleted
  - malformed voice manifest causes conservative keep + diagnostic
  - GC failure reports warning without restoring deleted voice

contract/delete_model_route_test.py
  - DELETE /v1/models/{voiceId} deletes installed voice
  - response separates removedArtifactIds and retainedArtifactIds
  - /v1/voices/installed no longer includes deleted voice after refresh
  - deleting one Kokoro preset keeps shared Kokoro artifact if another preset remains
```

### Decision

Use `voiceId` as the primary delete identity:

```text
DELETE /v1/models/{voiceId}
```

Then run artifact GC based on manifest reference counts.

This keeps deletion flexible across provider shapes, cleanly separates installed lifecycle from catalog/install/storage internals, modularizes GC, remains standalone from OpenAI compatibility, scales to shared artifacts, and is well-tested with shared-artifact deletion cases.

---

## Q37 — Registry refresh trigger: who calls `VoiceRegistry.refresh()`?

### Recommendation

Application services should call `VoiceRegistry.refresh()` after committed install/delete lifecycle changes.

Do not call refresh from API routes. Do not call refresh from stores.

Recommended rule:

```text
InstallService commits installed voice manifest
  -> calls VoiceRegistry.refresh()

DeleteModelService removes installed voice manifest
  -> calls VoiceRegistry.refresh()

VoiceStore
  -> only reads/writes/removes manifests

API routes
  -> only call application services
```

### Why application services are the right layer

`VoiceRegistry.refresh()` is not a transport concern and not a persistence concern. It is runtime routing cache synchronization after a durable voice lifecycle change.

The application service knows when the durable commit happened:

```text
InstallService knows voice manifest was committed.
DeleteModelService knows voice manifest was removed.
```

That makes it the correct orchestration layer.

### Why not API routes?

Routes should stay thin transport adapters:

```text
parse request
call service
map response/error
```

If routes call `VoiceRegistry.refresh()`, refresh behavior gets duplicated across routes and future callers. For example, a CLI install command, startup reconciler, or background retry would need to remember to call refresh separately. That is fragile.

### Why not stores?

Stores should be persistence-only:

```text
VoiceStore.write(manifest)
VoiceStore.remove(voiceId)
VoiceStore.list()
```

If `VoiceStore` triggers refresh, persistence gains runtime side effects. That makes tests harder, creates dependency cycles, and violates SoC. Stores should not know about runtime adapter routing.

### Recommended dependency shape

```text
InstallService
  -> CatalogRepository
  -> Downloader
  -> Verifier
  -> ArtifactStore
  -> VoiceStore
  -> VoiceRegistry.refresh()

DeleteModelService
  -> VoiceStore
  -> VoiceRegistry.refresh()
  -> ArtifactGarbageCollector

VoiceRegistry
  -> reads VoiceStore + ArtifactStore during refresh
```

The dependency is intentional: application services orchestrate stores and runtime cache.

### Refresh semantics

`VoiceRegistry.refresh()` should be copy-on-write as already established in architecture:

```text
build new routing map from installed manifests
validate referenced artifacts/descriptors
atomically swap routing map
active synthesis sessions keep their existing adapter/descriptor reference
```

This avoids corrupting active sessions during install/delete.

### Failure behavior

Refresh failure after commit must not roll back storage automatically.

Install case:

```text
voice manifest committed
refresh fails
-> job failed with install.refresh_failed_after_commit
-> voice remains durably installed
-> startup/retry can refresh later
```

Delete case:

```text
voice manifest removed
refresh fails
-> delete response includes delete.refresh_failed_after_commit warning/error
-> voice remains durably deleted
-> startup/retry can refresh later
```

Do not let runtime cache failure mutate durable storage. Storage is source of truth; registry is cache.

### Startup reconciliation

Startup should always refresh from durable stores:

```text
server startup
  -> VoiceRegistry.refresh()
  -> report diagnostics for invalid manifests/artifacts
  -> expose only valid routable voices
```

This gives the system a natural recovery path after refresh failure, process crash, or manual file repair.

### Test strategy

Minimum tests for this decision:

```text
unit/install_service_refresh_test.py
  - refresh called after voice manifest commit
  - refresh not called if install fails before commit
  - refresh failure does not delete committed manifest
  - job records install.refresh_failed_after_commit

unit/delete_service_refresh_test.py
  - refresh called after voice manifest removal
  - refresh not called if delete fails before removal
  - refresh failure does not restore deleted manifest
  - response records delete.refresh_failed_after_commit

unit/voice_store_no_side_effect_test.py
  - VoiceStore.write does not call refresh
  - VoiceStore.remove does not call refresh

contract/install_delete_refresh_test.py
  - installed voice appears in /v1/voices/installed after service refresh
  - deleted voice disappears after service refresh
  - startup refresh rebuilds registry from durable manifests
```

### Decision

Application services own refresh orchestration:

```text
InstallService/DeleteModelService -> VoiceRegistry.refresh()
```

Routes remain transport-only, stores remain persistence-only, and `VoiceRegistry` remains a rebuildable runtime cache. This keeps the design flexible, clean, modular, standalone from OpenAI compatibility, scalable to CLI/background callers, and well-tested around commit/refresh failure boundaries.

---

## Q38 — Installed voice manifest payload: concrete paths or logical artifact references?

### Recommendation

Persist **logical artifact references plus a payload template**, then hydrate concrete runtime paths during `VoiceRegistry.refresh()`.

Do not persist brittle absolute paths in installed voice manifests.

Recommended persisted voice manifest shape:

```python
class InstalledVoiceManifest(BaseModel):
    schema_version: Literal["1.0"]
    voice_id: str
    engine_id: str
    display_name: str
    language: str
    locale: str | None = None
    quality_tier: Literal["low", "medium", "high"]

    source_catalog_entry_id: str | None = None
    artifact_refs: list[str]
    payload_template: VoicePayloadTemplateUnion

    installed_at: datetime
```

Refresh hydrates it into a runtime descriptor:

```text
VoiceStore.list()
-> ArtifactStore.resolve(artifactRefs)
-> validate artifact manifests/files
-> hydrate VoiceDescriptor.payload with runtime paths/values
-> build copy-on-write routing map
```

The adapter still receives concrete usable values at synthesis time. The difference is that concrete values are produced at runtime from validated artifacts, not frozen into the durable voice manifest.

### Why not persist absolute paths?

Absolute paths are convenient at first, but they are fragile:

- app data directory may move;
- user may migrate install data between machines/accounts;
- artifact layout may change in a future version;
- tests using temp directories become noisy;
- reinstall/repair flows become harder;
- manifests become tied to one filesystem layout instead of logical installed state.

A voice manifest should describe **what voice is installed and which artifacts it needs**, not the current absolute path of every file.

### Identity and payload split

Recommended split:

```text
InstalledVoiceManifest
  -> durable installed voice identity and logical payload template

InstalledArtifactManifest
  -> durable artifact identity and relative file paths/hashes

VoiceRegistry.refresh()
  -> runtime hydration layer

VoiceDescriptor
  -> runtime adapter-facing descriptor with concrete usable payload
```

This keeps persistence stable and runtime execution practical.

### Payload template examples

Use template payloads that reference logical file roles or artifact IDs, not absolute paths.

Piper-plus persisted template:

```json
{
  "kind": "model-file-template",
  "modelArtifactRef": "piper-plus-vi_VM_meeting-medium-onnx-2026-06",
  "modelFileRole": "model",
  "configFileRole": "config"
}
```

Hydrated runtime payload:

```json
{
  "kind": "model-file",
  "modelPath": "/Users/.../artifacts/piper-plus/piper-plus-vi_VM_meeting-medium-onnx-2026-06/files/model.onnx",
  "configPath": "/Users/.../artifacts/piper-plus/piper-plus-vi_VM_meeting-medium-onnx-2026-06/files/config.json"
}
```

Kokoro persisted template:

```json
{
  "kind": "preset-template",
  "artifactRef": "kokoro-v1-onnx",
  "presetName": "af_bella"
}
```

Hydrated runtime payload:

```json
{
  "kind": "preset",
  "presetName": "af_bella",
  "modelPath": "/Users/.../artifacts/kokoro/kokoro-v1-onnx/files/model.onnx",
  "voicesPath": "/Users/.../artifacts/kokoro/kokoro-v1-onnx/files/voices.bin"
}
```

The exact hydrated payload can be engine-specific, but the hydration boundary stays generic.

### Hydration boundary

Recommended module:

```text
src/mery_tts/voices/hydration.py
```

Responsibilities:

```text
- accept InstalledVoiceManifest
- resolve artifact references through ArtifactStore
- validate required file roles exist
- build runtime VoiceDescriptor
- return structured diagnostics for missing/bad artifacts
```

Do not put hydration logic in API routes. Do not make adapters search the filesystem. Adapters should receive a resolved `VoiceDescriptor` and synthesize.

### Error and diagnostics behavior

If hydration fails during refresh:

```text
- skip that voice from runtime routing map
- keep the manifest on disk
- report diagnostic with voiceId, artifactRefs, missing role/file, reason
- do not crash the whole registry refresh if other voices are valid
```

Example diagnostic codes:

```text
voice_manifest.artifact_missing
voice_manifest.artifact_file_missing
voice_manifest.payload_template_invalid
voice_manifest.unsupported_payload_kind
voice_manifest.hydration_failed
```

This makes the system repairable. A broken voice should not take down all installed voices.

### Template versioning

Payload templates should be schema-versioned as part of the manifest. If needed later, add a template version field:

```python
class InstalledVoiceManifest(BaseModel):
    schema_version: Literal["1.0"]
    payload_template: VoicePayloadTemplateUnion
```

For first slice, manifest `schema_version` is enough. Add per-template version only if migrations become necessary.

### Test strategy

Minimum tests for this decision:

```text
unit/voice_payload_hydration_test.py
  - hydrates Piper model-file template into runtime model-file payload
  - hydrates Kokoro preset template into runtime preset payload
  - rejects template referencing missing artifact
  - rejects template referencing missing required file role
  - does not require absolute paths in persisted manifest

unit/voice_registry_hydration_test.py
  - refresh skips one broken voice but keeps valid voices routable
  - refresh emits diagnostics for hydration failure
  - moving app_data_dir with same relative artifact layout still hydrates

unit/installed_voice_manifest_schema_test.py
  - accepts artifactRefs + payloadTemplate
  - rejects absolute-path-only payload for persisted manifest
  - preserves canonical voiceId

contract/voices_installed_route_test.py
  - /v1/voices/installed returns hydrated/routable voices only
  - broken manifest appears in diagnostics, not installed voice list
```

### Decision

Persist logical references:

```text
voiceId + engineId + artifactRefs[] + payloadTemplate
```

Hydrate runtime descriptors during `VoiceRegistry.refresh()`:

```text
artifactRefs + artifact manifests -> concrete runtime VoiceDescriptor payload
```

This keeps manifests portable and stable, preserves clean SoC between persistence and runtime execution, modularizes engine-specific hydration, remains standalone from OpenAI compatibility, scales to provider layout changes, and is well-tested with temp-dir artifact stores.

---

## Q39 — First implementation slice: what exactly should be built first?

### Recommendation

Build **one vertical fake-catalog tracer bullet first**, not real downloads first.

The first slice should prove the full lifecycle with tiny local fixtures:

```text
bundled trusted catalog fixture
-> GET /v1/catalog/voices returns flat cards
-> POST /v1/models/install accepts catalogEntryId
-> creates durable async job
-> fake downloader/verifier installs fixture artifact into temp app_data_dir
-> writes artifact manifest
-> writes installed voice manifest
-> VoiceRegistry.refresh()
-> GET /v1/voices/installed shows the voice
-> DELETE /v1/models/{voiceId} removes it and GC runs
```

This is the highest-value first slice because it validates architecture boundaries and lifecycle semantics without depending on real provider URLs, large model files, or optional engine packages.

### Why fake catalog first

Real downloads introduce too many variables at once:

```text
network availability
provider URL stability
large binaries
engine package installation
platform-specific model behavior
slow tests
```

Those variables do not prove catalog/install architecture. They distract from it.

The first slice should prove the invariant:

```text
trusted catalog entry
-> verified artifact bytes
-> durable manifests
-> registry refresh
-> routable installed voice
-> safe deletion and artifact GC
```

Once that invariant is proven with fake fixtures, real Piper-plus/Kokoro entries become provider integration work, not architecture discovery.

### Scope of slice 1

Include:

```text
CatalogDocument schema
CatalogRepository for bundled fixture
CatalogTrustPolicy for bundled trusted catalog
CatalogQueryService projection to CatalogVoiceCard
InstallModelRequest with catalogEntryId
InstallJob model/state machine
FileInstallJobStore or temp-dir durable job store
InstallJobService enqueue
Deterministic test runner for jobs
FakeDownloader / fixture artifact copier
Verifier over fixture bytes
ArtifactStore atomic write
VoiceStore atomic write
VoiceRegistry.refresh() integration with hydrated fake voice
DeleteModelService + artifact GC
API contract tests
```

Exclude:

```text
remote catalog fetch
Ed25519 remote signing implementation, unless tiny unit-only helper already exists
real Piper-plus/Kokoro downloads
real engine synthesis
resume partial downloads
browser/UI install progress
automatic OpenAI alias install
voice cloning consent flows
```

### Concrete fixture design

Use a tiny fake voice entry that looks like real provider data but uses local bytes.

Example catalog IDs:

```text
catalogEntryId: fake-tts:demo-voice@fixture-v1
voiceId: fake-tts:demo-voice
engineId: fake-tts
artifactId: fake-tts-demo-artifact-v1
```

Fixture artifact files:

```text
tests/fixtures/catalog/fake-catalog-v1.json
tests/fixtures/artifacts/fake-model.bin
tests/fixtures/artifacts/fake-config.json
```

The fake adapter/registry path should be enough to expose the installed voice in `/v1/voices/installed`. Synthesis is not required for this slice unless existing fake synthesis fixtures make it trivial.

### API acceptance criteria

Slice 1 is done when these flows pass:

```text
GET /v1/catalog/voices
  -> returns fake-tts:demo-voice card
  -> includes catalogEntryId and voiceId separately
  -> installed=false before install

POST /v1/models/install { catalogEntryId }
  -> returns 202 + jobId
  -> durable job is created

Job runner executes
  -> resolves catalog entry
  -> verifies fixture bytes
  -> writes artifact manifest
  -> writes voice manifest
  -> refreshes VoiceRegistry
  -> job completed with voiceId/engineId/artifactIds

GET /v1/models/install/{jobId}
  -> returns completed job result

GET /v1/voices/installed
  -> includes fake-tts:demo-voice

DELETE /v1/models/{voiceId}
  -> removes installed voice manifest
  -> refreshes VoiceRegistry
  -> GC removes unreferenced fake artifact

GET /v1/voices/installed
  -> no longer includes fake-tts:demo-voice
```

### Test strategy

Minimum tests for this slice:

```text
contract/catalog_install_lifecycle_test.py
  - catalog lists fixture voice as installable
  - install starts async durable job
  - deterministic runner completes job
  - installed voice appears after refresh
  - delete removes voice and unreferenced artifact

unit/catalog_projection_test.py
  - normalized fake catalog projects to flat card

unit/install_job_store_test.py
  - durable job survives store reinitialization

unit/artifact_voice_store_test.py
  - artifact and voice manifests are atomic and parseable

unit/voice_registry_refresh_test.py
  - registry hydrates installed fake voice from logical artifact refs

unit/delete_gc_test.py
  - GC removes unreferenced fake artifact after voice delete
```

Use temp directories for app data in tests. Do not write into developer machine app data.

### Why this is scalable

The fake tracer bullet exercises the same seams real providers need:

```text
Piper-plus real entry -> same catalog/install/artifact/manifest path
Kokoro shared artifact -> same path, just different artifact_refs
VoxCPM2 multi-artifact -> same path, more artifact_refs
Remote catalog -> same repository interface, stricter trust policy
```

So the first slice is not throwaway. It is the skeleton every provider will use.

### Decision

Start implementation with one vertical fake-catalog lifecycle tracer bullet.

Only after that passes should real Piper-plus/Kokoro catalog entries and downloads be added.

This keeps the work flexible, clean, SoC-preserving, modular, standalone from provider availability, scalable to many provider shapes, and well-tested through deterministic lifecycle contract tests.

---

## Q40 — When is catalog/install hardening done enough to move on?

### Recommendation

Catalog/install hardening is done enough to move on when the **fake lifecycle is complete and one real provider catalog entry is validated**.

Do not require all providers. This feature should prove the platform lifecycle, not populate the entire roadmap catalog.

Recommended definition of done:

```text
1. Fake catalog lifecycle passes end-to-end.
2. Catalog/install/delete APIs have contract tests.
3. Job persistence survives service/store restart in tests.
4. Artifact and voice manifests use atomic writes.
5. Registry refresh exposes installed voices and hides deleted/broken voices.
6. Shared-artifact garbage collection is tested.
7. One real provider catalog entry is validated manually or under a marked test.
```

The preferred real provider validation is:

```text
Kokoro -> validates shared-artifact shape
```

Acceptable alternative:

```text
Piper-plus -> validates model-file voice shape
```

### Why not all providers?

Requiring all providers would turn this feature into catalog population and provider rollout. That is a different workstream.

Catalog/install hardening needs to prove these invariants:

```text
trusted catalog entry can be projected to API card
catalogEntryId can start durable async install job
verified artifacts can be stored atomically
installed voice manifest is the commit point
VoiceRegistry can hydrate and route installed voices
DELETE removes voice and GC handles unreferenced artifacts safely
```

Once those invariants hold, adding more providers should mostly mean adding catalog data and adapter-specific payload templates, not rewriting the install system.

### Real provider gate

The real provider gate should validate one non-fake shape after the fake lifecycle passes.

Recommended order:

1. **Kokoro** if available, because it proves shared artifacts and preset voices.
2. **Piper-plus** if Kokoro setup is harder, because it proves model-file voice artifacts.

Do not block done on both. Validate one, record the other as next rollout.

### Required tests

Minimum done-level test set:

```text
contract/catalog_install_lifecycle_test.py
  - fake catalog list -> install -> job complete -> installed voice -> delete -> GC

contract/catalog_routes_test.py
  - /v1/catalog/voices returns flat cards
  - cards include catalogEntryId and voiceId separately
  - cards hide raw download URL authority

contract/models_install_route_test.py
  - POST /v1/models/install returns 202 + jobId
  - GET /v1/models/install/{jobId} returns status/result/error
  - invalid catalogEntryId fails with native error

contract/delete_model_route_test.py
  - DELETE /v1/models/{voiceId} is idempotent
  - deleted voice disappears after refresh
  - shared artifact is retained while referenced

unit/install_job_store_test.py
  - durable job survives store reinitialization
  - active duplicate install returns existing job

unit/artifact_voice_store_test.py
  - atomic artifact manifest writes
  - atomic voice manifest writes
  - partial writes do not become canonical state

unit/voice_registry_hydration_test.py
  - logical payload templates hydrate to runtime descriptors
  - broken voice manifest is skipped and diagnosed

marked/real_provider_catalog_test.py
  - one Kokoro or Piper-plus catalog entry validates against schema
  - optional install path works when provider fixture/deps are available
```

### Explicit non-goals for done

Do not include these in the done gate:

```text
all 19 provider catalog entries
remote catalog refresh scheduler
full Ed25519 production key rotation
resume partial downloads
UI install progress screen
voice cloning consent flow
OpenAI alias auto-install
GPU/backend selection
full storage migration system
```

Those are follow-up slices or later feature grills.

### Closeout decision

Catalog/install hardening is complete enough to move on when:

```text
fake lifecycle proves the full architecture
+ one real provider entry proves the design maps to reality
```

This keeps the feature flexible, clean, SoC-preserving, modular, standalone from provider rollout, scalable to many providers, and well-tested without letting scope explode.

---

## Catalog/install grill closeout

Final recommended sequence from Q28–Q40:

```text
Q28  Full registry flywheel target, tracer-bulleted
Q29  Install by catalogEntryId only
Q30  Normalized signed catalog internally, flat voice cards externally
Q31  Bundled vs remote trust tiers
Q32  Async install jobs always
Q33  Durable local job store behind protocol
Q34  Artifact IDs separate from voice IDs
Q35  Installed voice manifest is commit point
Q36  Delete by voiceId, GC unreferenced artifacts
Q37  Application services trigger VoiceRegistry.refresh()
Q38  Persist logical payload templates, hydrate runtime paths on refresh
Q39  First slice is fake-catalog lifecycle tracer bullet
Q40  Done = fake lifecycle + one real provider entry validated
```

Next recommended feature after this grill: **provider rollout strategy**, starting with which real catalog entries/adapters to add after the fake lifecycle proves the platform.
