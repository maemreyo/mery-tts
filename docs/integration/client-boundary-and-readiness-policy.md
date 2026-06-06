# Client boundary and readiness policy

**Status:** Implemented
**Date:** 2026-06-06
**Related:** ADR-0001, ADR-0021, ADR-0025, ADR-0026

## Overview

This document describes how clients consume Mery setup and readiness without owning
provider install logic. It applies to Zam Reader, Mery Console, Mery CLI, and all
future clients.

## Responsibilities

### Mery owns

- Provider runtime installation, detection, and repair
- Artifact download, verification, and storage
- Voice manifest management
- Smoke testing and diagnostics
- Readiness truth derivation (unavailable / degraded / ready / unpaired / incompatible)
- Setup intent validation and install confirmation
- Local user consent for all install actions

### Clients own

- Detecting when Mery is unavailable or degraded (via `/v1/health`)
- Presenting setup options to the user
- Opening Mery setup intent URLs
- Polling readiness after setup handoff
- Deciding when to use Mery synthesis vs. fallback (e.g., Web Speech)
- Presentation and UX of voice selection

## Setup contract

All clients use the same setup flow:

```text
Client detects Mery unavailable/degraded via /v1/health
  → Client offers local voice setup to user
  → Client opens Mery setup URL: /console/setup?client=<id>&intent=<intent>
  → Mery Console validates intent and shows recommendations
  → User confirms installation in Mery (Console or CLI)
  → Mery installs provider runtime, artifacts, voices, runs smoke
  → Client polls /v1/health until ready
  → Client uses /v1/audio/speech when readiness policy allows
```

## Zam Reader example

```text
Zam Reader checks /v1/health
  → status: "degraded" (no usable voices)
  → User clicks "Set up local voices"
  → Zam Reader opens: http://127.0.0.1:8765/console/setup?client=zam-reader&intent=english-reading
  → Mery Console shows recommended English reading voice packs
  → User confirms in Mery Console
  → Zam Reader polls /v1/health every 5s
  → status: "ready" → Zam Reader switches to /v1/audio/speech
```

## Generic client example

```text
My Desktop App checks /v1/health
  → status: "unavailable"
  → App shows "Set up Mery for offline voices"
  → App opens: http://127.0.0.1:8765/console/setup?client=my-app&intent=general
  → Mery Console shows available voice packs
  → User confirms in Mery CLI: mery voice-packs install en-reading
  → App polls /v1/health
  → status: "ready" → App uses /v1/audio/speech
```

## Fallback policy

Zam Reader Web Speech fallback policy is a Zam Reader concern, not a Mery dependency.
Mery provides readiness truth; clients decide fallback behavior.

- When Mery is `unavailable` or `unpaired`: clients MUST use fallback
- When Mery is `degraded`: clients MAY use experimental local synthesis at their own risk
- When Mery is `ready`: clients SHOULD use Mery synthesis
- When Mery is `incompatible`: clients MUST use fallback and report version mismatch

## Cross-references

- ADR-0001 — Product / ownership boundary
- ADR-0021 — Local Zam Reader usable milestone
- ADR-0025 — Readiness, health, smoke, and Zam Reader gating
- ADR-0026 — Standalone setup boundary and client responsibilities
