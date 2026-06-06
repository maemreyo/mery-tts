# Zam Reader readiness polling policy

**Status:** Implemented
**Date:** 2026-06-06
**Related:** ADR-0021, ADR-0025, ADR-0026, ADR-0030

## Overview

This document defines how Zam Reader should poll Mery readiness after setup handoff
and when it may switch from Web Speech fallback to Mery synthesis.

## Readiness states and client behavior

| `/v1/health` status | Zam Reader behavior |
|---|---|
| `unavailable` | Use Web Speech. Do not attempt local synthesis. Offer setup. |
| `unpaired` | Use Web Speech. Show pairing instructions. |
| `incompatible` | Use Web Speech. Show version mismatch warning. |
| `degraded` | Use Web Speech by default. MAY offer experimental local synthesis with user consent. |
| `ready` | Use `/v1/audio/speech`. Local synthesis is preferred. |

## Polling strategy

After opening Mery setup URL, Zam Reader should poll `/v1/health` at regular intervals:

- Initial poll delay: 2 seconds after setup URL is opened
- Poll interval: 5 seconds
- Maximum poll duration: 10 minutes (then show timeout message)
- Stop polling when status transitions to `ready` or user cancels

## Polling response contract

```json
{
  "schema_version": "v1",
  "status": "ready",
  "helper_id": "mery-xxxx",
  "helper_version": "0.1.0",
  "contract_version": "v1",
  "engines": [
    {
      "engine_id": "piper-plus",
      "dependency_status": "available",
      "installed_voice_count": 2,
      "usable_voice_count": 2,
      "smoked_voice_count": 2,
      "smoke_passed_count": 2,
      "smoke_failed_count": 0,
      "status": "available"
    }
  ],
  "total_usable_voices": 2,
  "total_installed_voices": 2
}
```

## Decision outcomes

| Condition | Action |
|---|---|
| `status == "ready"` AND `total_usable_voices > 0` | Switch to `/v1/audio/speech` |
| `status == "ready"` AND `total_usable_voices == 0` | Stay on Web Speech (no usable voices) |
| `status == "degraded"` AND user enabled experimental | MAY try `/v1/audio/speech` with fallback |
| `status == "degraded"` AND no experimental flag | Stay on Web Speech |
| `status == "unavailable"` | Stay on Web Speech |
| `status == "unpaired"` | Show pairing flow |
| `status == "incompatible"` | Show version update prompt |

## Cross-references

- ADR-0021 — Local Zam Reader usable milestone
- ADR-0025 — Readiness, health, smoke, and Zam Reader gating
- ADR-0026 — Standalone setup boundary and client responsibilities
- ADR-0030 — Zam Reader guided setup handoff
- [`client-boundary-and-readiness-policy.md`](./client-boundary-and-readiness-policy.md)
