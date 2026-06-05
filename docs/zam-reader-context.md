# Zam Reader — Context for the Helper Repo

This file exists so anyone reading `mery-tts-server` understands what Zam Reader is and why this helper exists.

## What is Zam Reader?

Zam Reader is a **WXT-based Manifest V3 browser extension** (Firefox-first, also Chrome/Edge/Brave/Cốc Cốc). It is a personal teaching toolkit for a Vietnamese teacher who teaches English.

Key properties:

- Local-first, zero tracking, GPLv3.
- Free core is zero-network.
- v1 is standalone, extendable, cross-platform.
- Strict architecture: `domain/`, `ports/`, `adapters/`, `features/`, `background-only/`, `entrypoints/`.
- i18n is Vietnamese-only in v1 UI.
- No WXT auto-imports; boundaries are enforced by depcruise and CI.

## What does Zam Reader do today?

Zam Reader helps learners read real English content on the web. It provides:

- reader overlay with tap-word lookup;
- dictionary lookup;
- vocab save/review;
- annotations;
- light progress mirror;
- TTS via the Web Speech API for read-aloud and pronounce.

## Why does this helper exist?

Zam Reader's current TTS uses the browser's Web Speech API. That is fine for free-core zero-network behavior, but voice quality and language coverage vary by browser/OS.

This helper exists to provide an **optional, higher-quality, locally managed TTS runtime** that Zam Reader can bridge to when the user explicitly opts in.

## The boundary

```text
Zam Reader (browser extension)
  -> LocalTTSProvider
  -> LocalTTSBridge
  -> LocalhostTransport / future NativeMessagingTransport
  -> Mery TTS Server (this repo)
```

Rules:

- Zam Reader never imports Python/helper code.
- Zam Reader talks to this helper only through the versioned `/v1` contract.
- This helper owns native binaries, models, engines, catalog, cache, checksums, pairing, security, and local playback services.
- Zam Reader owns extension UI, provider registry integration, fallback to Web Speech, and extension-side structured error handling.

## Where to learn more

- Zam Reader source: `../zreader/`
- Zam Reader ADRs: `../zreader/docs/adr/`
- Zam Reader TTS/audio context: `../zreader/docs/reports/tts-feature-exploration.md` and `../zreader/docs/reports/tts-grill-followup-decisions.md`
- Helper design decisions: `./docs/reports/local-tts-helper-design-decisions.md`
- Helper readiness contract: `./docs/integration/zam-reader-readiness-contract.md`

## What this helper must not assume

- It must not assume Zam Reader is the only client.
- It must not assume a specific browser.
- It must not assume Zam Reader's internal architecture.
- It must not assume the user has a GPU.
- It must not assume the user has an Apple Developer signing budget.
