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

## Catalog signing mechanism

**Algorithm: Ed25519** (via Python `cryptography` library).

Rationale:
- Modern, fast, 32-byte keys, no parameter tuning
- `cryptography` is already a transitive dep of most Python security stacks
- Signing is offline (maintainer CI/local); verification is online but cheap
- Avoids symmetric HMAC (requires secret distribution) and RSA (larger keys, padding choices)

**Key management:**
- Private key lives only on the maintainer machine / CI secrets — never in the repo
- Public key is hardcoded in `security/catalog_pubkey.py` as a `bytes` constant
- Rotating the public key requires a package release (intentional — key rotation is a trust event)

**What is signed:**
- The catalog JSON **with the `signature` field omitted**, serialized as canonical UTF-8 JSON
  (`json.dumps(catalog_without_sig, sort_keys=True, ensure_ascii=False).encode()`)
- Signature stored as lowercase hex in the `signature` field of the catalog JSON

**`catalog/verifier.py` contract:**

```python
class CatalogVerifier:
    def verify_remote(self, catalog_json: bytes) -> CatalogData:
        """Verify Ed25519 signature, schema, expiry. Raises LocalTTSError on failure."""

    def load_bundled(self, catalog_path: Path) -> CatalogData:
        """Load and schema-validate bundled catalog. No signature check — trusted by installation."""
```

SoC: `CatalogVerifier` owns cryptographic verification. `CatalogLoader` owns file I/O.
Neither touches `api/`, `engines/`, or `models/`.

## Bundled vs remote catalog trust policy

```text
Bundled catalog (checked into repo, ships with the package)
  -> trust model: trusted by installation
     (if attacker can tamper catalog-v1.json they already own the installed package)
  -> verification: schema validation + expiry check only — NO signature check
  -> on first run: copied to data dir
  -> used for offline / first-run catalog browsing

Remote catalog (explicit user action only)
  -> trust model: untrusted until Ed25519 signature verified against bundled public key
  -> verification: Ed25519 signature + schema + expiry — ALL three required
  -> triggered by: zam-tts catalog refresh or Zam Reader Options "Refresh catalog"
  -> stored as remote-catalog.json alongside bundled
  -> never fetched automatically — always explicit user action
```

The distinction from "zero-network reading behavior" must be clear in UI copy.

**Why bundled needs no signature:** Defense-in-depth argument does not hold here —
adding signature verification for bundled catalog requires shipping the private key
or a separate signing step in the build pipeline, for zero actual security gain.
The threat model for bundled catalog is package tamper; that is already mitigated by
package integrity (checksums at the package manager level, e.g. uv lockfile hashes).

## Consequences

**Enables:**
- Remote catalog MITM attacks are defeated even if the CDN or catalog host is compromised
- Bundled catalog is simple to update — no signing ceremony for in-repo edits
- `CatalogVerifier` has a clean two-method interface: `verify_remote()` vs `load_bundled()`
- Tests can run against a fixture catalog with a test Ed25519 keypair (generated in `conftest.py`)
- Offline users can install bundled catalog voices without any network

**Constrains:**
- Every remote catalog release requires the maintainer to sign with the private key
- Public key rotation requires a package release (intentional — it is a trust event)
- Every catalog update requires recalculating SHA256 + sizeBytes for every model file
- Allowlist changes require a code release (intentional)
- `CatalogVerifier` must be tested with: valid signature, invalid signature, wrong key,
  expired catalog, schema mismatch, wrong-host, wrong-checksum, wrong-size scenarios

## Related

- ADR-0001 (helper owns downloads, not Zam Reader)
- `docs/integration/zam-reader-readiness-contract.md` §5, §14
