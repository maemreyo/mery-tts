# ADR-0007 — Signed catalog + per-file checksums + download allowlist

**Status:** Accepted  
**Date:** 2026-06-05  
**Source:** Design Decision 14, 6

## Context

The helper downloads model files (38–350 MB) onto the user's machine. This is a
security boundary. How do we ensure catalog data and downloaded files are trustworthy?

## Decision

Use **three layers of integrity**: signed/versioned catalog + per-file SHA256 + 
download host allowlist.

## Catalog schema requirements

```json
{
  "catalogId": "zam-tts-curated-v1",
  "schemaVersion": "1.0",
  "catalogVersion": "1.0.0",
  "createdAt": "2026-06-05T00:00:00Z",
  "expiresAt": "2027-06-05T00:00:00Z",
  "signature": "...",
  "models": [
    {
      "modelId": "piper-plus.en-us.lessac.medium",
      "engineId": "piper-plus",
      "displayName": "English — Lessac Medium",
      "language": "English",
      "locale": "en-US",
      "qualityTier": "medium",
      "recommendedFor": ["lightweight", "english", "offline"],
      "files": [
        {
          "url": "https://huggingface.co/rhasspy/piper-voices/...",
          "sha256": "...",
          "sizeBytes": 63897600,
          "fileRole": "model"
        },
        {
          "url": "https://huggingface.co/rhasspy/piper-voices/...",
          "sha256": "...",
          "sizeBytes": 4096,
          "fileRole": "config"
        }
      ],
      "license": "MIT",
      "source": "rhasspy/piper-voices"
    }
  ]
}
```

## Download rules

1. Client sends `modelId` — never a raw URL
2. Helper resolves the URL from the catalog internally
3. Verify URL is on the allowlist before any network request
4. Download to `cache/temp/` first; never write directly to model store
5. After download: verify SHA256 and sizeBytes match catalog
6. On verify success: atomic move to `models/{engineId}/{modelId}/`
7. On verify failure: delete temp file, emit `install.failed` with `model.checksum_mismatch`

## Allowlisted download hosts (initial set)

```text
huggingface.co
cdn-lfs.huggingface.co
github.com
objects.githubusercontent.com
```

Any request to a non-allowlisted host is rejected with `catalog.host_not_allowed`.

## Vietnamese model note

The piper-plus Vietnamese model has HuggingFace path `vi/vi_VM_meeting/medium/`
but is cataloged with locale `vi-VN` in our normalized schema. The `fileRole: model`
file is `vi_VM_meeting-medium.onnx` and `fileRole: config` is
`vi_VM_meeting-medium.onnx.json`. These are distinct from the locale string.

## Bundled vs remote catalog

```text
Bundled catalog (checked into repo, always available)
  -> ships with the package
  -> copied to data dir on first run
  -> curated English + Vietnamese + other recommended voices
  -> used for offline / first-run catalog browsing

Remote catalog (explicit user action only)
  -> user triggers: zam-tts catalog refresh
  -> helper fetches from configured remote URL
  -> validates schema + signature + expiry
  -> stores as remote-catalog.json alongside bundled
  -> Zam Reader Options page offers "Refresh catalog" button
```

Remote refresh is **never automatic**. It is always an explicit user action.
The distinction from "zero-network reading behavior" must be clear in UI copy.

## Consequences

**Enables:**
- Model downloads are safe even if the catalog source is compromised (checksum barrier)
- Offline users can install bundled catalog voices without any network
- Tests can run against a fixture catalog with fake checksums and a mock download server

**Constrains:**
- Every catalog update requires recalculating SHA256 + sizeBytes for every model file
- Allowlist changes require a code release (this is intentional)
- `CatalogVerifier` must be tested with expired, unsigned, wrong-host, wrong-checksum,
  and wrong-size scenarios

## Related

- ADR-0001 (helper owns downloads, not Zam Reader)
- `docs/integration/zam-reader-readiness-contract.md` §5, §14
