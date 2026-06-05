# TTS Grill Follow-up Decisions — Audio UX + Architecture

**Date:** 2026-06-05
**Scope:** Running decision log after ADR-0028 through ADR-0032. Use this report to resume TTS/audio grilling without relying on chat context.

## Canonical artifacts

- Exploration report: `docs/reports/tts-feature-exploration.md`
- Follow-up ADR: `docs/adr/0033-audio-session-ux-architecture-contracts.md`
- Follow-up roadmap folder: `.scratch/roadmap/0033-audio-session-ux-architecture-contracts/`

## Q40-Q80 summary

Q40-Q80 are accepted and captured in ADR-0033:

- Audio Panel is session-first and mode-aware.
- Smart Listen is promoted only when local eligibility signals justify it.
- Smart Listen uses split CTA: `Bắt đầu nghe` and `Xem các đoạn`.
- Playlist uses progressive disclosure and contextual actions.
- Mini-player is bottom-docked, safe-area aware, reduced-motion friendly, and focuses the active sentence from excerpt interaction.
- Empty/loading/error states are contextual.
- `src/features/audio/` was initially planned as the audio boundary, later refined by Q81.
- Provider-neutral TTS contracts and playback controller/reducer are required.
- Playback events and learning artifact events are separate.
- Checkpoints are lightweight local resume state; artifacts are DataService/RxDB learning evidence.
- Plans are immutable; runtime state is separate.
- `PlanAugmentation` overlays refine labels/reasons/hints without reordering visible plans.
- Augmentation cache is keyed by article/content hash + planner/augmentation/provider/model versions.
- Planner scoring uses a versioned `ScoringProfile`.
- Sentence anchors are reader-overlay-owned; audio consumes sentence IDs/planned sentences.
- Tests follow a layered pyramid.

## Q81 — Cross-feature listening contracts

**Decision:** Promote shared listening contracts to `src/domain/listening` and `src/ports/listening`; `src/features/audio` becomes implementation/orchestration/adapters, not the contract owner.

Target structure:

```txt
src/domain/listening/
  PlaybackState.ts
  PlaybackCommand.ts
  PlaybackEvent.ts
  ListeningPlan.ts
  ListeningSessionState.ts
  PlannedSentence.ts
  LearningArtifact.ts
  ScoringProfile.ts
  composeAudioSessionViewModel.ts

src/ports/listening/
  TTSProvider.ts
  ListeningCheckpointStore.ts
  ListeningArtifactSink.ts
  PlanAugmentationStore.ts

src/features/audio/
  planning/
  playback/
  orchestration/
  adapters/

src/features/reader-overlay/
  components/audio/
  hooks/audio/
  adapters/sentenceAnchors/
```

Rules:

- `reader-overlay` may import `src/domain/listening` and `src/ports/listening`.
- `reader-overlay` must not import `src/features/audio` internals.
- `src/features/audio` must not import reader-overlay DOM/highlight modules.
- Cross-feature communication uses shared domain state/events and injected ports, not feature-to-feature imports.
- `CONTEXT.md` should document **Listening contracts** as shared domain/port contracts.

## Q82 — Sentence highlight/scroll seam

**Decision:** Audio emits `PlaybackEvent`; `reader-overlay` subscribes and maps events to highlight/follow actions. Add imperative UI command adapter later only if needed.

Rules:

- Audio does not call DOM/highlight/scroll ports directly.
- `reader-overlay` owns sentence highlight, word highlight, adaptive follow scroll, reduced-motion behavior, excerpt focus, and Return-to-current-sentence behavior.
- `PlaybackEvent.utteranceStarted` drives active sentence highlight.
- `PlaybackEvent.wordBoundary` drives word highlight only when provider capability and reduced-motion allow.
- `PlaybackEvent.error` drives recoverable Audio Panel/Mini-player error UI.

## Q83 — Command/event split

**Decision:** Split `PlaybackCommand` and `PlaybackEvent`.

Commands are user/system intents into the controller. Events are facts emitted by controller/provider and consumed by reducers/subscribers.

```ts
type PlaybackCommand =
  | { type: 'play'; planId: string; startAt?: SentenceCursor; source: PlaybackCommandSource }
  | { type: 'pause'; source: PlaybackCommandSource }
  | { type: 'resume'; source: PlaybackCommandSource }
  | { type: 'stop'; source: PlaybackCommandSource }
  | { type: 'skip-sentence'; source: PlaybackCommandSource }
  | { type: 'retry-sentence'; source: PlaybackCommandSource }
  | { type: 'set-rate'; rate: number; scope: 'session' | 'current-sentence'; source: PlaybackCommandSource };
```

## Q84 — Accepted-command events

**Decision:** Controller emits command-accepted facts immediately so UI is responsive without duplicated optimistic state.

Events include accepted facts such as `play-accepted`, `pause-accepted`, `resume-accepted`, `stop-accepted`, `skip-accepted`, `retry-accepted`, and `rate-change-accepted`, followed by lifecycle facts such as `utterance-started`, `paused`, `resumed`, `stopped`, `done`, `error`, and `word-boundary`.

State implications:

- `play-accepted` → `preparing`
- `pause-accepted` → `pausing`
- `resume-accepted` → `resuming`
- `stop-accepted` → `stopping`

## Q85 — SentenceCursor shape

**Decision:** Runtime cursor uses stable IDs only; checkpoint/artifact boundaries may add recovery metadata.

```ts
type SentenceCursor = {
  planId: string;
  segmentId: string;
  sentenceId: string;
};

type CheckpointCursor = SentenceCursor & {
  segmentIndex: number;
  sentenceIndex: number;
  sentenceTextHash: string;
  normalizedOffset: number;
};
```

## Q86 — Playback vs session state

**Decision:** Keep `PlaybackState` and `ListeningSessionState` separate; compose a pure UI read model.

```ts
type AudioSessionViewModel = {
  plan: ListeningPlan;
  session: ListeningSessionState;
  playback: PlaybackState;
  activeCursor?: SentenceCursor;
  activeSegment?: ListeningSegment;
  activeSentence?: PlannedSentence;
  progress: {
    completedSegments: number;
    totalSegments: number;
    completedSentences: number;
    totalSentences: number;
    estimatedRemainingMs?: number;
  };
  ui: {
    primaryAction: 'play' | 'pause' | 'resume' | 'retry' | 'stop';
    canSkip: boolean;
    canReplay: boolean;
    canPin: boolean;
    followSuspended: boolean;
    errorMessageKey?: string;
  };
};
```

## Q87 — View model composition ownership

**Decision:** Domain owns pure structural composer; reader-overlay owns presentation wrapper.

- `src/domain/listening/composeAudioSessionViewModel.ts` has no DOM, i18n, reduced-motion, or layout flags.
- `src/features/reader-overlay/hooks/audio/useAudioSessionPresentation.ts` adds i18n copy, labels/tooltips, reduced-motion/layout, excerpt focus, and follow behavior.

## Q88 — Serializable session state

**Decision:** `ListeningSessionState` uses readonly arrays, not Sets.

```ts
type ListeningSessionState = {
  planId: string;
  removedSegmentIds: readonly string[];
  completedSegmentIds: readonly string[];
  pinnedSentenceIds: readonly string[];
  replayedSentenceIds: readonly string[];
  baselineRate: number;
  temporaryRate?: {
    sentenceId: string;
    rate: number;
    reason: 'slow-this-sentence';
  };
};
```

Reducers enforce uniqueness and stable ordering. Selectors may build local Sets.

## Q89 — Serializable playback state

**Decision:** Public `PlaybackState` is JSON-serializable; controller owns private effectful handles.

No provider handles, functions, DOM refs, timers, native utterances, or raw `Error` objects are allowed in public state.

```ts
type PlaybackState =
  | { status: 'idle' }
  | { status: 'preparing'; cursor: SentenceCursor }
  | { status: 'playing'; cursor: SentenceCursor; rate: number }
  | { status: 'pausing'; cursor: SentenceCursor }
  | { status: 'paused'; cursor: SentenceCursor }
  | { status: 'resuming'; cursor: SentenceCursor }
  | { status: 'stopping'; cursor?: SentenceCursor }
  | { status: 'done' }
  | { status: 'error'; cursor?: SentenceCursor; messageKey: string; recoverable: boolean };
```

## Q90 — Error payloads

**Decision:** Playback errors store `messageKey` + structured metadata, not user-facing text.

```ts
type PlaybackError = {
  messageKey:
    | 'audio.error.unsupported'
    | 'audio.error.voiceUnavailable'
    | 'audio.error.synthesisFailed'
    | 'audio.error.interrupted'
    | 'audio.error.boundaryUnavailable'
    | 'audio.error.providerUnavailable';
  recoverable: boolean;
  cursor?: SentenceCursor;
  providerCode?: string;
  cause?: 'unsupported-api' | 'no-voice' | 'provider-error' | 'user-stop' | 'unexpected';
};
```

## Q91 — Audio i18n namespace

**Decision:** Create `src/i18n/vi/audio.json` for Audio Panel, Mini-player, Smart Listen, playback errors, empty states, and speed labels.

`reader.json` keeps general reader overlay copy. Split later only if audio namespace grows too large.

## Q92-Q94 — Command source and creators

**Decision:** Commands carry semantic action type plus optional non-identifying source metadata; public UI command creators require source; command creators live in reader-overlay presentation layer.

```ts
type PlaybackCommandSource =
  | 'audio-panel'
  | 'mini-player'
  | 'keyboard'
  | 'article-excerpt'
  | 'system-resume'
  | 'controller';
```

Rules:

- No translated labels in commands.
- No URL, raw text, user identifier, analytics payload, or behavioral tracking.
- Domain defines command types only.
- `src/features/reader-overlay/hooks/audio/audioCommandCreators.ts` creates UI commands and enforces source.
- Internal controller/system commands use explicit `controller` or `system-resume` source.

## Q95 — State reducers vs event sourcing

**Decision:** Current-state reducers are source of truth; persist only meaningful learning artifacts.

- Playback/session events are transient inputs.
- Checkpoints store resumable summary, not full event logs.
- Persist artifacts such as `listen-again-sentence`, `segment-completed`, `saved-word-audio-exposure`, `review-promoted`, later `shadowing-attempt`.
- Optional debug ring buffer is in-memory only.

## Q96-Q99 — Audio diagnostics

**Decision:** Use shared dev-only diagnostics service at `src/shared/diagnostics/audioDiagnostics.ts`.

```ts
type AudioDiagnosticMetadata = Record<string, string | number | boolean>;

type AudioDiagnosticCode =
  | 'audio.command.accepted'
  | 'audio.command.rejected'
  | 'audio.playback.utteranceStarted'
  | 'audio.playback.utteranceEnded'
  | 'audio.playback.paused'
  | 'audio.playback.error'
  | 'audio.provider.callback'
  | 'audio.session.artifactQueued'
  | 'audio.session.artifactFlushed';

type AudioDiagnosticEntry = {
  at: string;
  code: AudioDiagnosticCode;
  source: 'controller' | 'orchestrator' | 'provider-adapter';
  kind: 'command' | 'playback-event' | 'session-event' | 'provider-callback' | 'error';
  cursor?: SentenceCursor;
  metadata?: AudioDiagnosticMetadata;
};
```

Rules:

- Diagnostics are shared dev tooling, not domain model and not product port.
- Default sink is no-op.
- Dev/test sink may keep an in-memory ring buffer.
- Metadata is shallow scalar only; no nested objects/arrays/unknown/raw `Error`/DOM/provider payload/prompts/article text/page URL/API keys/user IDs/mic data.
- Use internal diagnostic codes, not i18n keys.
- Sanitizer lives with diagnostics and fails closed.

## Current resume point

Q81-Q99 are accepted and should be reflected in ADR-0033 plus roadmap issue acceptance criteria before more grilling. Next unresolved seam starts at Q101.
