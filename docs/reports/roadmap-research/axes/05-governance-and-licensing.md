# Axis 05 — Governance & Licensing (HIDDEN)

**Last updated:** 2026-06-05
**Status in roadmap:** **Not listed** — discovered via research
**Why it matters:** Community catalog with voice cloning without governance = legal/PR disaster. EU AI Act (Aug 2026), state laws, content moderation all apply.

---

## What this axis covers

The legal, ethical, and operational policies Mery needs around voice cloning, content moderation, license tracking, and provenance. This is **a hidden axis that gates the "Ollama for TTS" community catalog feature.**

## The legal landscape (2026)

### EU AI Act
- **Effective:** August 2026
- **Requirement:** Disclosure of synthetic audio
- **Implication for Mery:** Any community voice that is cloned/generated must be tagged as such in the manifest. User must be informed when audio is synthetic.
- **Source:** [EU AI Act overview](https://artificialintelligenceact.eu/)

### State laws (US)
- **Texas:** Voice cloning without consent is illegal (effective 2024)
- **Tennessee:** ELVIS Act (Ensuring Likeness, Voice, and Image Security) — voice is property
- **California:** Pending legislation similar to TX/TN
- **Implication for Mery:** Cloned voices of identifiable real people = legal liability

### Industry standards

| Standard | What it does | Mery relevance |
|---|---|---|
| **SPDX 3.0 AI Profile** | Machine-readable license metadata for AI models | License tracking in voice manifest |
| **CAP specification** (veritaschain) | Content / Creative AI Profile — three conformance levels (Bronze/Silver/Gold), Safe Refusal Provenance | Voice consent + provenance |
| **C2PA** | Content authenticity (image leading, audio emerging) | Audio provenance metadata |
| **AudioSeal** (Meta) | Inaudible watermarking for generated audio | Embed provenance in audio stream |

## Voice cloning consent framework

Required for any community-uploaded cloned voice:

```yaml
consent:
  type: cloned  # vs synthetic
  reference_audio_sha256: "abc123..."
  consent_record_url: "https://..."  # off-platform signed record
  voice_owner: "Jane Doe"
  voice_owner_contact: "jane@example.com"
  scopes: [commercial_use, educational_use]  # not: political_use, deepfake_use
  geographic_scope: [worldwide]  # or specific regions
  expiration: 2028-01-01  # or perpetual
  revocable: true
  revocation_process: "https://..."  # URL to takedown flow
  recorded_at: 2026-01-15
  recorded_by: "Voice Studio Inc."
  signature: "ed25519:..."
```

**Consent must be:**
1. **Granular by use type**: "Voice cloning" ≠ "General TTS" ≠ "Political content"
2. **Time-bounded**: expiration dates
3. **Scope-specific**: geographic, commercial, educational
4. **Revocable**: clear revocation process
5. **Linkable to evidence**: document timestamp, signatory authority

**MFA reference:** [SEC Framework - AI Voice Consent](https://www.sec.gov/files/ctf-written-input-costa-031926.pdf)

## Content moderation pipeline

```
Upload → Format validation → License check → NSFW detection
       → Deepfake detection (voice encoder similarity to known voices)
       → Reference audio hash check
       → Manual review (if flagged)
       → Publish OR Reject
```

**Technical approaches:**
1. **Audio watermarking**: AudioSeal embeds inaudible markers at inference time
2. **Voice encoder verification**: Compare embedding to known voiceprints (Resemblyzer)
3. **NSFW detection**: Audio classification models (limited availability)
4. **Reference audio validation**: SHA256 + signed consent record

## License tracking

Mery voice manifest should include SPDX 3.0 AI Profile fields:

```json
{
  "spdxId": "SPDXRef-MERY-VOICE-001",
  "name": "mery-voice-emma",
  "downloadLocation": "https://registry.mery.ai/voices/emma:v1",
  "relationship": [
    {"relationshipType": "hasConcludedLicense", "licenseId": "CC-BY-4.0"}
  ],
  "ai:trainingData": {
    "datasetName": "LibriSpeech",
    "license": "CC-BY-4.0"
  }
}
```

**License options for community voices:**
- MIT (most permissive)
- Apache 2.0 (permissive + patent grant)
- CC-BY-4.0 (attribution)
- CC-BY-NC-4.0 (non-commercial — research only)
- CC-BY-SA-4.0 (copyleft)
- Custom (with full text in manifest)

## DMCA / takedown process

Required: clear contact + designated agent registration + 3-strike policy + appeal mechanism.

```
1. Notice received (legal@mery.ai)
2. Verify claimant identity + claim
3. Takedown (move to taken_down state, archive only)
4. Notify contributor
5. Contributor can appeal with counter-notice
6. Restore or permanent removal
```

## Provenance / signing

**Options:**
1. **Sigstore / cosign** — container-style attestation for models
2. **in-toto** — cryptographic attestation chain
3. **C2PA** — content authenticity for audio (emerging)
4. **Ed25519 keys** (Ollama-compatible) — simpler, proven

**Recommendation for Mery MVP:** Ed25519 keys (Ollama pattern). Mery signs voice manifests with Mery's private key. Users verify with Mery's public key bundled in the install. Add Sigstore later for stronger guarantees.

## Tier classification

| Sub-item | Tier | Mery's priority |
|---|---|---|
| SPDX license metadata | Tier 2 COMMON (any model registry) | P0 (manifest schema) |
| Ed25519 signing | Tier 2 COMMON | P0 (manifest integrity) |
| Voice cloning consent records | Tier 1 BASE (legal) | **P0 before community catalog** |
| EU AI Act disclosure metadata | Tier 1 BASE (legal) | **P0** |
| AudioSeal watermarking | Tier 3 PROVIDER-SPECIFIC | P2 (added after P0 ships) |
| C2PA provenance | Tier 3 PROVIDER-SPECIFIC | P3 (ecosystem-dependent) |
| DMCA takedown process | Tier 1 BASE (legal) | P0 (operational) |
| Deepfake detection at upload | Tier 2 COMMON | P1 (when community catalog opens) |

## Reference projects

- [spdxai/spdx-3-model](https://spdxai.github.io/) — license tracking standard
- [veritaschain/cap-spec](https://github.com/veritaschain/cap-spec) — content AI profile
- [C2PA](https://c2pa.org/) — content authenticity
- [facebookresearch/audioseal](https://github.com/facebookresearch/audioseal) — audio watermarking
- [EU AI Act](https://artificialintelligenceact.eu/) — full text and obligations
- [Ollama signing model](https://docs.ollama.com/import) — practical reference for Ed25519 pattern

## Decisions needed (BEFORE community catalog opens)

1. **Cloned voices allowed in community catalog?**
   - **If yes:** require consent record (per schema above), manual review, scoped license
   - **If no:** synthetic-only (engine output, no reference audio) — much simpler
2. **License whitelist or any license?**
   - Whitelist is safer (only SPDX-approved licenses)
   - Any license = user responsibility
3. **Who reviews uploads?** (mery team, community moderators, automated?)
4. **Takedown SLA?** (24h for DMCA, 7d for community flags?)
5. **Geographic restrictions?** (Some jurisdictions require different handling)

**Recommendation:** **Ship community catalog with synthetic voices only first.** Add cloned-voice support only after governance ADR is in place + a moderation pipeline is operational. This is the same sequencing as ElevenLabs.

## Cross-references

- `axes/03-ecosystem.md` — model registry (the feature this gates)
- `axes/01-engine-layer.md` — voice cloning engine capability
- `99-priority-matrix.md` — sequencing
