# TTS Feature — Exhaustive Exploration Report

**Date:** 2026-06-04
**Scope:** End-to-end mapping of the Read-Aloud / Pronounce (TTS) feature, from
engine to all wiring points, in Zam Reader v1.
**Method:** Direct source read across 18 files + 4 parallel background research
agents (engine internals, UI wiring, messaging protocol, docs/ADRs) +
cross-validation.

**Follow-up artifacts:** This exploration was converted into ADRs and roadmap
issues after the TTS grilling session.

- ADR-0028 — [TTS Evolution: Strategic Scope and Free/Pro Boundary](../adr/0028-tts-evolution-scope.md)
- ADR-0029 — [Smart Listening Loop](../adr/0029-smart-listening-loop.md)
- ADR-0030 — [Listenability Lens](../adr/0030-listenability.md)
- ADR-0031 — [Pronunciation Coach Phasing](../adr/0031-pronunciation-coach.md)
- ADR-0032 — [TTS Reliability and Core Hardening](../adr/0032-tts-reliability-core-hardening.md)
- Roadmap issues live under `.scratch/roadmap/0028-tts-evolution-scope/`,
  `.scratch/roadmap/0029-smart-listening-loop/`, `.scratch/roadmap/0030-listenability/`,
  `.scratch/roadmap/0031-pronunciation-coach/`, and
  `.scratch/roadmap/0032-tts-reliability-core-hardening/`.

---

## 0. Executive Summary

Zam Reader implements TTS **exclusively via the Web Speech API** (ADR-0008) —
no cloud TTS, no API keys, no network. The entire feature runs in the **content
script** through `window.speechSynthesis`; **no messages** flow through
`services/messaging/protocol.ts` or `entrypoints/background.ts`.

Two distinct user-facing entry points exist:

1. **Read-aloud an article** — sentence-by-sentence with karaoke highlighting
   (`useReadAloud` + `createKaraoke`)
2. **Pronounce a single lookup word** — one-off utterance from `LookupCard`
   (`useVoiceSettings.speakLookup`)

A third, separate reading mode — **RSVP** — exists but is timer-based (no TTS
involved). It re-uses the `rsvpWords` memo from `useReadAloud` but does not
touch `speechSynthesis`.

| Metric | Value |
|---|---|
| Source files (TTS surface) | 18 |
| ADR primary | 1 (`0008-tts-karaoke.md`) |
| ADRs with TTS constraints | 7 |
| i18n keys (vi only) | 10 |
| Tests across 7 files | 14 |
| Chrome message types | 0 |
| `chrome.storage` calls | 0 |
| Offscreen documents | 0 |
| Boundary crossings | 0 (TTS is content-script-local) |

---

## 1. Architectural Insight — TTS Bypasses the Extension Boundary

TTS is **deliberately** content-script-local. Rationale (cross-referenced from
ADR-0012, ADR-0013):

- `window.speechSynthesis` is available in content scripts.
- TTS makes no network requests → free-core zero-network invariant
  (`freeCoreZeroNetwork.test.tsx` proves `fetch` is never called) holds
  trivially.
- The messaging protocol (`protocol.ts`) is reserved for *data* services
  (lookupDictionary, saveVocab, AI, progress). TTS does not appear.
- TTS settings live in `localStorage` (content-script accessible), not
  `chrome.storage` (background-only). This is a deliberate trade-off: no
  cross-device sync, but trivial implementation.

**Consequence:** when the content script unloads (page navigation, overlay
close mid-session), audio continues playing until the browser stops it. The
karaoke state machine has no teardown hook.

---

## 2. File Inventory

```
src/
├── entrypoints/
│   ├── background.ts            (13 LOC) — NO TTS handling
│   └── reader.content.ts        (41 LOC) — mounts overlay; NO TTS
├── features/reader-overlay/
│   ├── overlay.tsx              (29 LOC) — mountReaderOverlay entry
│   ├── ReaderOverlayApp.tsx     (1348 LOC) — orchestrator; ~30 TTS lines
│   ├── lib/
│   │   ├── readerCommands.ts    (34 LOC) — keyboard commands incl. readAloud
│   │   ├── reading/             — TTS ENGINE
│   │   │   ├── index.ts         (barrel)
│   │   │   ├── types.ts         (28 LOC) — TTSProvider, Karaoke*, Highlight
│   │   │   ├── ttsProvider.ts   (11 LOC) — Web Speech adapter
│   │   │   ├── karaoke.ts       (77 LOC) — sentence driver
│   │   │   ├── highlight.ts     (128 LOC) — DOM/CSS-Highlight engine
│   │   │   └── bionicReading.ts (110 LOC) — co-located; NOT TTS
│   │   └── text/
│   │       ├── index.ts
│   │       └── sentenceSplitter.ts (31 LOC) — Intl.Segmenter
│   ├── hooks/
│   │   ├── useReadAloud.ts         (91 LOC) — read-aloud orchestrator
│   │   ├── useVoiceSettings.ts     (86 LOC) — voice picker + speakLookup
│   │   ├── useReaderPreferences.ts (103 LOC) — ttsRate persistence
│   │   └── useKeyboardShortcuts.ts (25 LOC) — generic dispatch
│   └── components/
│       ├── chrome/
│       │   └── Toolbar.tsx         (180 LOC) — Play/Pause/Stop buttons
│       ├── reading/
│       │   ├── ReaderControls.tsx  (431 LOC) — voice select + rate slider
│       │   └── RSVPReader.tsx      (114 LOC) — timer-based, NOT TTS
│       └── lookup/
│           ├── LookupCard.tsx      (175 LOC) — pronounce button
│           └── VoiceHint.tsx       (29 LOC)  — **ORPHAN, see §13.1**
├── security/
│   └── __tests__/freeCoreZeroNetwork.test.tsx — TTS = part of free core
└── i18n/vi/common.json              — 10 TTS keys
```

---

## 3. Engine Layer — `lib/reading/`

### 3.1 `ttsProvider.ts` (11 LOC)

```ts
export function createWebSpeechTTSProvider(speechSynthesis: SpeechSynthesis): TTSProvider
```

Thin wrapper. **Only implementation** of `TTSProvider` — no cloud, no
offscreen, no `chrome.tts`.

| Method | Maps to |
|---|---|
| `speak(utterance)` | `speechSynthesis.speak(utterance)` |
| `pause()` | `speechSynthesis.pause()` |
| `resume()` | `speechSynthesis.resume()` |
| `stop()` | `speechSynthesis.cancel()` |
| `supportsWordBoundary` | `'onboundary' in SpeechSynthesisUtterance.prototype` |

### 3.2 `types.ts` (28 LOC)

```ts
export type TTSProvider = {
  speak(utterance: SpeechSynthesisUtterance): void;
  pause(): void;
  resume(): void;
  stop(): void;
  readonly supportsWordBoundary: boolean;
};

export type KaraokeEvent =
  | { type: 'sentence-start'; index: number }
  | { type: 'sentence-end'; index: number }
  | { type: 'word-start'; index: number; charIndex: number; charLength: number }
  | { type: 'done' };

export type KaraokeController = {
  start(): void;
  pause(): void;
  resume(): void;
  stop(): void;
  onEvent(callback: (event: KaraokeEvent) => void): () => void;
};

export type HighlightManager = {
  setActiveSentence(index: number): void;
  setActiveWord(charIndex: number, charLength: number): void;
  clear(): void;
  readonly reducedMotion: boolean;
};
```

### 3.3 `karaoke.ts` (77 LOC) — sentence driver

**State:** `listeners: Set`, `currentIndex: number`, `stopped: boolean`.

**Lifecycle / state machine:**

```
start()
  ├── stopped = false, currentIndex = 0
  ├── if sentences.length === 0 → emit 'done', return
  └── speakSentence(0)

speakSentence(i)
  ├── if stopped || i >= length → emit 'done', return
  ├── currentIndex = i
  ├── new SpeechSynthesisUtterance(sentences[i])
  ├── set voice + lang + rate
  ├── onstart     → emit 'sentence-start'
  ├── onend       → emit 'sentence-end' → speakSentence(i+1) [recursive]
  ├── onboundary  → emit 'word-start' (only if supportsWordBoundary && name === 'word')
  └── provider.speak(utterance)

pause()  → provider.pause()
resume() → provider.resume()
stop()   → stopped = true; provider.stop(); emit 'done'
```

**Event handlers from Web Speech NOT used:**
`onerror`, `onpause`, `onresume`, `onmark`, sentence-boundary `onboundary`.

**Edge cases handled:** empty sentences, stop-mid-playback, missing
word-boundary support, non-`'word'` boundary names.

**Edge cases skipped (see §13.5):** error recovery, sentence-boundary
events, per-voice word-boundary detection, rate validation, `reducedMotion`
plumbing.

### 3.4 `highlight.ts` (128 LOC) — DOM highlight engine

`createHighlightManager(article, sentences)` performs **destructive
mutation** of the article element: replaces its children with
`<span data-zr-sentence-index="N">` separated by `' '` text nodes. Stores
`originalText` for restoration.

**Two highlight paths:**

| Capability | API | Fallback |
|---|---|---|
| `'highlights' in CSS` (Chrome 105+) | `new Highlight()` + `CSS.highlights.set('zr-word', h)` | — |
| Otherwise | — | `<mark class="zr-active-word">` wrap + `article.replaceChildren(...)` |

`clear()` is special: when `sentenceSpans.length === 0` it restores
`article.textContent = originalText`; otherwise it only strips CSS classes.

**`reducedMotion`** is read from `prefers-reduced-motion` via `matchMedia`
and exposed on the returned `HighlightManager.reducedMotion`, but
**`karaoke.ts` never consumes it** (see §13.5).

### 3.5 `bionicReading.ts` (110 LOC)

Co-located but unrelated to TTS. Bolds first-N letters of each word.
Re-exported from the same barrel for organizational reasons.

### 3.6 `index.ts` (barrel)

```ts
export { createHighlightManager, createKaraoke, createWebSpeechTTSProvider } from ...;
export type { HighlightManager, KaraokeController, KaraokeEvent, TTSProvider } from ...;
```

---

## 4. Text Layer — `lib/text/`

### 4.1 `sentenceSplitter.ts` (31 LOC) — `splitSentences(text)`

- **Primary:** `new Intl.Segmenter('en', { granularity: 'sentence' })`
  (per ADR-0005 reuse).
- **Fallback:** regex `[^.!?]+[.!?]+|[^.!?]+$`.
- **Post-process:** `mergeNonTerminalAbbreviations` — glues segments
  following `Mr. Mrs. Ms. Dr. Prof. Sr. Jr. St.` to the next segment.

---

## 5. React Hooks Layer

### 5.1 `useReadAloud.ts` (91 LOC)

**Signature:**
```ts
useReadAloud(
  result: ExtractionResult,
  tr: (key: string) => string,
  selectedVoice: SpeechSynthesisVoice | null,
  articleRef: RefObject<HTMLElement | null>,
  ttsRate = 1.0,
)
```

**State owned:**
- `sentences` = `useMemo(() => splitSentences(result.textContent), [result])`
- `readAloudDisabled` = `sentences.length === 0 || !('speechSynthesis' in window) || !('SpeechSynthesisUtterance' in window)`
- `readAloudHidden / pauseReadAloudHidden / stopReadAloudHidden` — UI flags
- `pauseReadAloudLabel` — toggles `tr('pauseReadAloud')` ↔ `tr('resumeReadAloud')`
- `rsvpWords` = `useMemo(() => result.textContent.split(/\s+/u).filter(Boolean), [result])`
- 2 refs: `highlightManagerRef`, `karaokeRef`

**API returned:**
| Method | Action |
|---|---|
| `handleReadAloud()` | `clear()` existing highlight → `createHighlightManager(article, sentences)` → `createWebSpeechTTSProvider(window.speechSynthesis)` → `createKaraoke({sentences, provider, voice, rate})` → subscribe events → `start()`; flip flags |
| `handlePauseReadAloud()` | `karaokeRef.current?.pause()`; set label to `'resumeReadAloud'` |
| `handleResumeReadAloud()` | `karaokeRef.current?.resume()`; restore label |
| `handleStopReadAloud()` | `karaokeRef.current?.stop()` |

**Event routing:**

```
sentence-start → highlightManager.setActiveSentence(index)
word-start     → highlightManager.setActiveWord(charIndex, charLength)
done           → highlightManager.clear() + reset UI flags
```

### 5.2 `useVoiceSettings.ts` (86 LOC)

**`localStorage` keys:**
- `zr.tts.voiceName` — selected voice name
- `zr.tts.macVoiceHintDismissed` — Mac hint dismissed

**State:**
- `voices` = `useMemo(() => englishVoices(), [])` — filtered by
  `voice.lang.toLowerCase().startsWith('en')`
- `showMacVoiceHint` — `navigator.platform.includes('mac')` AND not
  dismissed
- `selectedVoiceName` — saved name or first voice's name

**API returned:**
- `voices`, `selectedVoiceObj`, `selectedVoiceName`
- `handleVoiceChange(name)` — localStorage write + state update
- `handleDismissMacVoiceHint()` — localStorage write + hide hint
- `speakLookup(result)` — **separate TTS path**; validates `result.type === 'hit'`
  and `entry.lemma`; creates a single utterance directly (no karaoke,
  no highlight)

### 5.3 `useReaderPreferences.ts` (103 LOC)

`ReaderPreferences.ttsRate: number` (clamped 0.5–2.0) is stored in
`localStorage['zr.reader.prefs']` and applied via CSS custom properties
on the shadow host. **Decoupled** from `useVoiceSettings` (architectural
smell — see §13.7).

### 5.4 `useKeyboardShortcuts.ts` (25 LOC)

Generic dispatch from `READER_COMMANDS` registry. All keys joined into a
single string for `useHotkeys`. `enableOnFormTags: false`,
`preventDefault: true`.

---

## 6. UI Components

### 6.1 `chrome/Toolbar.tsx` (180 LOC) — TTS controls

| Button | `data-zr` attribute | Visibility | onClick |
|---|---|---|---|
| Read | `data-zr-read-aloud` (icon `Play`) | `!readAloudHidden` | `onReadAloud` |
| Pause | `data-zr-pause-read-aloud` (icon `Pause`) | `!pauseReadAloudHidden` | `onPauseReadAloud`; **`onDoubleClick` → `onDoubleClickPause`** |
| Stop | `data-zr-stop-read-aloud` (icon `Square`) | `!stopReadAloudHidden` | `onStopReadAloud` |

Default visibility: `readAloudHidden=false`, `pauseReadAloudHidden=true`,
`stopReadAloudHidden=true`. After `handleReadAloud` → readAloud flips to
hidden, pause+stop appear. After `done` → flip back.

### 6.2 `reading/ReaderControls.tsx` (431 LOC) — settings popover

**`<FullReaderSettings>` Audio section:**
- Voice `<select data-zr-voice>` — **only rendered when
  `voices.length > 0`** (consequence: empty voice list hides the picker)
- TTS rate `<SliderRow>` — min 0.5, max 2.0, step 0.1, display `1.5×`
- Mac voice hint — `<div className="zr-voice-hint-inline">` with
  `[data-zr-dismiss-voice-hint]`

`QuickReadingPopover` (opened with `q`) **does not** contain an audio
section.

`ReaderControls` is a backward-compat alias for `FullReaderSettings`.

### 6.3 `lookup/LookupCard.tsx` (175 LOC) — pronounce button

```tsx
<button
  data-zr-pronounce
  aria-label="Nghe phát âm"
  disabled={pronounceDisabled || isLoading}
  onClick={onPronounce}
  icon={<Volume2 />}
/>
```

`pronounceDisabled` in `ReaderOverlayApp.tsx:1204` = `voices.length === 0`.

### 6.4 `lookup/VoiceHint.tsx` (29 LOC) — **ORPHAN COMPONENT**

Standalone `<aside className="zr-voice-hint">` using i18n key
`reader.macVoiceHint` (long text). Uses `flushSync` on dismiss. **Not
imported anywhere in production code** (verified: `ReaderOverlayApp.tsx`
does not reference it). Only tests reference it.

Production uses the **inline variant** in `ReaderControls.tsx`
(`<div className="zr-voice-hint-inline">`, key `reader.macVoiceHintShort`)
instead.

### 6.5 `reading/RSVPReader.tsx` (114 LOC) — NOT TTS

Timer-based word display using `setInterval`. Re-uses `rsvpWords` memo
from `useReadAloud` but does not invoke `speechSynthesis`. WPM 100–700.

---

## 7. Top-level Wiring — `ReaderOverlayApp.tsx`

### 7.1 Imports (lines 66, 70)

```ts
import { useReadAloud } from "./hooks/useReadAloud";
import { useVoiceSettings } from "./hooks/useVoiceSettings";
```

### 7.2 Hook calls (lines 228–245)

```ts
const { preferences, handleChange: handlePreferencesChange } =
  useReaderPreferences(shadowRoot);
const {
  voices, showMacVoiceHint, selectedVoiceName, selectedVoiceObj,
  handleVoiceChange, handleDismissMacVoiceHint, speakLookup,
} = useVoiceSettings();
const readAloud = useReadAloud(
  result, tr, selectedVoiceObj, articleRef, preferences.ttsRate,
);
```

### 7.3 Keyboard command handlers (lines 972–973)

```ts
readAloud: readAloud.handleReadAloud,
stopReadAloud: readAloud.handleStopReadAloud,
// pauseReadAloud is NOT in READER_COMMANDS — see §13.4
```

### 7.4 Toolbar props (lines 1003–1011)

```tsx
<Toolbar
  onReadAloud={readAloud.handleReadAloud}
  onPauseReadAloud={readAloud.handlePauseReadAloud}
  onDoubleClickPause={readAloud.handleResumeReadAloud}
  onStopReadAloud={readAloud.handleStopReadAloud}
  readAloudDisabled={readAloud.readAloudDisabled}
  readAloudHidden={readAloud.readAloudHidden}
  pauseReadAloudHidden={readAloud.pauseReadAloudHidden}
  stopReadAloudHidden={readAloud.stopReadAloudHidden}
  pauseReadAloudLabel={readAloud.pauseReadAloudLabel}
  ...
/>
```

### 7.5 LookupCard pronounce (line 1205)

```tsx
<LookupCard
  ...
  pronounceDisabled={voices.length === 0}
  onPronounce={() => speakLookup(lookup.currentLookup)}
  ...
/>
```

### 7.6 `FullReaderSettings` voice props (lines 1237–1241)

```tsx
voices={voices.map((v) => ({ name: v.name }))}
selectedVoiceName={selectedVoiceName}
onVoiceChange={handleVoiceChange}
showMacVoiceHint={showMacVoiceHint}
onDismissMacVoiceHint={handleDismissMacVoiceHint}
```

Note: only `name` is forwarded — `lang` is dropped. The settings component
is not aware of voice language.

---

## 8. Command Registry — `lib/readerCommands.ts`

| ID | Label (vi) | Shortcut |
|---|---|---|
| `readAloud` | "Đọc bài" | `r` |
| `stopReadAloud` | "Dừng đọc" | `s` |
| `dismissPanel` | "Đóng panel tra từ" | `Escape` (collides with `close`) |

**Pause is not a command.** Only bound via the Toolbar button + double-click.
This is an architectural inconsistency (see §13.4).

---

## 9. Entry Points & Boundary

| File | TTS involvement |
|---|---|
| `entrypoints/background.ts` (13 LOC) | **None.** Only registers DataService port + reader activation. |
| `entrypoints/reader.content.ts` (41 LOC) | **None directly.** Mounts shadow-root UI via `mountReaderOverlay`. |
| `services/messaging/protocol.ts` | **No TTS message types.** 0 matches in grep. Protocol is data-only. |
| `services/messaging/dataServiceClient.ts` | Unrelated (vocab, annotations, AI). |
| `overlay.tsx` (29 LOC) | Trivial mount of `<ReaderOverlayApp>`. |
| `chrome.storage.*` | **0 calls** in TTS code. |
| `chrome.offscreen.*` | **0 calls** in TTS code. |
| `chrome.runtime.connect` ports | Only `'data-service'`. No TTS port. |

---

## 10. ADR Constraints (7 ADRs binding TTS)

| ADR | Constraint |
|---|---|
| **0008** | Web Speech API only; IPA primary anchor; sentence-level baseline via `onstart/onend`; word-level upgrade via `onboundary` with runtime detection; no timer estimation. |
| **0004** | `TTSProvider` is a thin seam with one implementation (per ADR-0004, matches `supportsWordBoundary` capability pattern). |
| **0005** | Sentence splitting must use `Intl.Segmenter` (TTS karaoke reuses it). |
| **0007** | IPA data source for `LookupCard` 🔊 button. |
| **0011** | Best EN voice auto-selected on first use. |
| **0012** | TTS does not need browser permissions. |
| **0013** | "No TTS voice → hide 🔊, still show IPA." Implemented: `pronounceDisabled={voices.length === 0}`, voice select hidden when empty. |
| **0023** | `prefers-reduced-motion` applies to karaoke animation. Implemented in `highlight.ts` but **not wired** into `karaoke.ts` (see §13.5). |
| **0024** | TTS voice/rate belongs in **Reader Profile**. `ttsRate` is in `useReaderPreferences`; `voice` is **separately** in `useVoiceSettings` (architectural smell). |
| **0026** | `start/stop TTS` must be a Reader Command. Implemented: `readAloud` (`r`) + `stopReadAloud` (`s`). `pauseReadAloud` is not a command (see §13.4). |

---

## 11. i18n Keys (Vietnamese only — no `en/` exists)

| Key | Value |
|---|---|
| `reader.readAloud` | "Đọc bài" |
| `reader.pauseReadAloud` | "Tạm dừng" |
| `reader.resumeReadAloud` | "Đọc tiếp" |
| `reader.stopReadAloud` | "Dừng đọc" |
| `reader.pronounce` | "Nghe phát âm" |
| `reader.voice` | "Giọng đọc" |
| `reader.ttsRate` | "Tốc độ đọc" |
| `reader.macVoiceHint` | "macOS: hãy cài thêm giọng đọc chất lượng cao trong Cài đặt hệ thống để phát âm tự nhiên hơn." |
| `reader.macVoiceHintShort` | "macOS: Cài giọng chất lượng cao trong Cài đặt hệ thống để phát âm tự nhiên hơn." |
| `reader.dismiss` | "Ẩn" |

Two Mac-hint variants: long (`macVoiceHint` for `VoiceHint.tsx` orphan),
short (`macVoiceHintShort` for inline settings popover).

Per ADR-0018: Vietnamese-only v1 UI. No English fallback.

---

## 12. Test Coverage — Behavioral Contract

| File | TTS tests | What is verified |
|---|---|---|
| `__tests__/ttsProvider.test.ts` | 1 | Delegation of speak/pause/resume/stop; `supportsWordBoundary` flag. |
| `__tests__/karaoke.test.ts` | 3 | Sentence flow (start→end→chain→done); stop suppresses chain; word-boundary gating. |
| `__tests__/highlight.test.ts` | 3 | Active sentence toggle; reduced motion class; active word wrap/unwrap. |
| `__tests__/overlay.test.ts` (TTS portion) | 4 | Voice picker + persistence; no-EN fallback + disabled pronounce; Mac hint dismiss; sentence-by-sentence highlight; word-boundary DOM mutation. |
| `__tests__/components.test.tsx` | 1 | Toolbar preserves `data-zr-read-aloud`/`pause`/`stop`. |
| `__tests__/shortcuts.test.ts` | 1 | `readAloud` + `stopReadAloud` exist in `READER_COMMANDS`. |
| `__tests__/freeCoreZeroNetwork.test.tsx` | 1 | TTS speak called once; `fetch` not called. |

**Total: 14 TTS tests across 7 files.**

**Coverage gaps:**
- No test for pause→resume cycle
- No test for voice-change-mid-session
- No test for `onerror` recovery
- No test for empty-sentences `done` emission
- No test for `onEvent` unsubscribe
- No test for rate > 2.0 / < 0.5 boundaries
- No test for `useVoiceSettings.speakLookup` flow

---

## 13. Findings (15 items, severity-ordered)

### 13.1 `[LOW] Dead component — VoiceHint.tsx`

`src/features/reader-overlay/components/lookup/VoiceHint.tsx` is not
imported by any production file. It exists for tests only. The production
code uses an inline variant in `ReaderControls.tsx` (key
`macVoiceHintShort`). Either delete the orphan or wire it into the body
area (it was likely intended as a one-time body-level notice before the
inline variant was added).

### 13.2 `[MED] No `onerror` handler in karaoke.ts`

If the Web Speech API throws (voice unavailable, cancelled, quota), the
karaoke controller silently dies. `stopped` stays `false`, no `done` is
emitted, the UI's "Play" button stays hidden, the user sees nothing
happen. **Severity is medium** because the user can still navigate to
"Stop" but Stop is hidden too in this state. Fix: add
`utterance.onerror = () => emit({ type: 'done' })` so the UI always
recovers.

### 13.3 `[MED] No `voiceschanged` listener in useVoiceSettings`

`englishVoices()` runs once at mount via `useMemo([])`. On Chrome/Firefox
the `speechSynthesis.getVoices()` API is **async** — the first call often
returns `[]`, the list populates later via the `voiceschanged` event.
**Effect:** on first overlay open the voice list is empty, the voice
`<select>` is hidden (per `ReaderControls.tsx: {voices.length > 0 && ...}`),
the user cannot pick a voice, the `pronounce` button in `LookupCard` is
disabled (`voices.length === 0`). Fix: subscribe to
`speechSynthesis.addEventListener('voiceschanged', ...)` and re-derive.

### 13.4 `[MED] `pauseReadAloud` is not a Reader Command`

`READER_COMMANDS` has `readAloud` (`r`) and `stopReadAloud` (`s`), but
**not** `pauseReadAloud`. Pause can only be reached via the Toolbar
button (mouse) or double-clicking pause (undocumented UX). No keyboard
shortcut. Inconsistent with ADR-0026 ("start/stop TTS must be a Reader
Command" — pause arguably belongs in the set). Fix: add
`pauseReadAloud: { id, label, shortcut: ['p'] }` and wire in
`ReaderOverlayApp.tsx`.

### 13.5 `[MED] `reducedMotion` is defined but not honored in karaoke.ts`

`HighlightManager.reducedMotion` is read in `highlight.ts:prefersReducedMotion()`
and exposed, but `karaoke.ts` never imports or checks it. The Web Speech
word-highlight continues to mutate DOM even when the user prefers reduced
motion. ADR-0023 mandates this. Fix: pass a `reducedMotion: boolean` flag
into `createKaraoke` and skip emitting `word-start` events (or downgrade
to sentence-only) when true.

### 13.6 `[LOW] Voice + rate captured at `handleReadAloud` time, not reactive`

`useReadAloud` takes `selectedVoice` and `ttsRate` as arguments. The
captured values are used to construct the utterance in
`speakSentence(index)`. Changing voice or rate in settings mid-session
has no effect until the user starts a new session. Fix: store voice + rate
in refs and read them at `speakSentence` call time.

### 13.7 `[LOW] Architectural smell: voice settings not in Reader Profile`

ADR-0024 places TTS voice/rate in **Reader Profile**. `ttsRate` is in
`useReaderPreferences` (correct), but `voice` (and Mac hint) are in
`useVoiceSettings` (separate hook, separate `localStorage` namespace).
Two localStorage keys, two state machines, two sources of truth.
Consider consolidating into one `useReaderProfile` hook.

### 13.8 `[LOW] `speakLookup` re-derives voice; can diverge from saved preference`

`speakLookup` calls `selectedVoice(englishVoices())` afresh on each
invocation, **not** the hook's tracked `selectedVoiceObj`. If
`useVoiceSettings` were ever fixed to listen to `voiceschanged` (see
§13.3), `speakLookup` would still use the unfiltered helper and could
pick a different voice than what `useReadAloud` uses.

### 13.9 `[LOW] `speakLookup` uses unsafe `as unknown` cast**

```ts
const entry = (result as unknown as { entry: { lemma: string } }).entry;
```

The earlier `'type' in result` guard is on the result, not the entry.
Replace with a type-narrowing helper:
```ts
function isLookupHit(r: unknown): r is { entry: { lemma: string } } {
  return !!r && typeof r === 'object' && 'type' in r
    && (r as { type: unknown }).type === 'hit'
    && 'entry' in r
    && !!((r as { entry: unknown }).entry as { lemma?: string })?.lemma;
}
```

### 13.10 `[LOW] `useReadAloud` `useCallback` deps missing `tr` and `ttsRate` change listener`

`handleReadAloud` deps: `[articleRef, readAloudDisabled, sentences, selectedVoice]`.
Missing: `tr` (so the i18n key for `pauseReadAloudLabel` doesn't refresh
on locale change), `ttsRate` (intentionally captured — see §13.6), voice
change (same).

### 13.11 `[LOW] No unmount cleanup in `useReadAloud` or `useVoiceSettings`**

If the overlay closes mid-read-aloud, the `karaokeRef` listeners stay
registered, `highlightManagerRef` DOM mutations remain (article is
replaced by spans with the `data-zr-sentence-index` attributes). A
subsequent overlay open (toggle) will not tear down the old karaoke.
Fix: add `useEffect(() => () => karaokeRef.current?.stop(), [])` and a
mirror for the highlight manager (`article.textContent = originalText`).

### 13.12 `[LOW] `pauseReadAloudLabel` is UI-only state, not bound to `speechSynthesis.paused`**

The label toggles to "Đọc tiếp" on pause, back to "Tạm dừng" on resume.
If the user pauses, then the sentence ends naturally (browser race),
the label says "Đọc tiếp" but the karaoke is `done`. The `done` handler
in `useReadAloud` resets the flag buttons but **not** the label. Fix:
reset `pauseReadAloudLabel` to `tr('pauseReadAloud')` in the `done`
branch.

### 13.13 `[INFO] `onDoubleClickPause` → `handleResumeReadAloud` is undocumented UX**

The Toolbar's pause button has `onDoubleClick={onDoubleClickPause}` which
maps to `readAloud.handleResumeReadAloud` in `ReaderOverlayApp.tsx`.
Single click = pause, double click = resume. Not in any ADR, no tests
exercise this path. Either document it or remove it (a Resume button
might be clearer UI).

### 13.14 `[INFO] TTS is content-script-local; no `chrome.tts` API, no offscreen document`

The codebase uses `window.speechSynthesis` only. No use of
`chrome.tts` (the Chrome extension TTS API) or `chrome.offscreen` (MV3
offscreen document for service-worker-context TTS). Acceptable because
content scripts have direct access to Web Speech, but limits future
options (e.g., background-driven TTS scheduling).

### 13.15 `[INFO] RSVP `rsvpWords` re-use couples reading mode to TTS hook state**

`useReadAloud` exposes `rsvpWords` (split by whitespace) as a side
product for `RSVPReader`. This is a convenience but creates an
unintended coupling: opening RSVP requires `useReadAloud` to have run,
which requires `articleRef`, `selectedVoice`, `ttsRate`. Decoupling
(`splitWords(result.textContent)` extracted to `lib/text/`) would
cleaner.

---

## 14. Data Flow — `Read This Article Aloud`

```
User clicks Play (Toolbar, [data-zr-read-aloud])
  → onReadAloud prop
  → readAloud.handleReadAloud (useReadAloud)
    ├── articleRef.current → createHighlightManager(article, sentences)
    │   └── destructively replace article children with sentence spans
    ├── createWebSpeechTTSProvider(window.speechSynthesis)
    │   └── TTSProvider wrapper (no-op aside from method delegation)
    ├── createKaraoke({ sentences, provider, voice, rate })
    │   └── attaches listeners
    │       sentence-start → highlightManager.setActiveSentence(index)
    │       word-start     → highlightManager.setActiveWord(charIndex, charLength)
    │       done           → highlightManager.clear() + reset UI flags
    ├── setHidden flags: readAloud=true, pause+stop=false
    └── karaoke.start()
        └── speakSentence(0)
            ├── new SpeechSynthesisUtterance(sentences[0])
            ├── utterance.voice = voice; utterance.lang = voice.lang; utterance.rate = rate
            ├── onstart     → emit('sentence-start', 0)
            ├── onend       → emit('sentence-end', 0) → speakSentence(1) [recursive]
            ├── onboundary  → emit('word-start', ...) [if supports]
            └── provider.speak(utterance)
                └── window.speechSynthesis.speak(utterance) ← actual audio
```

## 15. Data Flow — `Pronounce This Word`

```
User clicks Pronounce (LookupCard, [data-zr-pronounce])
  → onPronounce prop
  → speakLookup(lookup.currentLookup) (useVoiceSettings)
    ├── validate: result.type === 'hit' + speechSynthesis available
    ├── selectedVoice(englishVoices())  ← re-derives, see §13.8
    ├── new SpeechSynthesisUtterance(entry.lemma)
    ├── utterance.lang = voice.lang; utterance.voice = voice
    └── window.speechSynthesis.speak(utterance) ← direct, no karaoke
```

---

## 16. Wiring Diagram (text form)

```
ReaderOverlayApp (TOP-LEVEL, 1348 LOC)
│
├── useVoiceSettings()                [lib: useVoiceSettings.ts]
│   ├── voices, selectedVoiceObj
│   │   ├── → useReadAloud (selectedVoiceObj)
│   │   ├── → FullReaderSettings (voices.map(name-only), selectedVoiceName)
│   │   └── → LookupCard (pronounceDisabled = voices.length === 0)
│   ├── handleVoiceChange             → FullReaderSettings (onVoiceChange)
│   ├── handleDismissMacVoiceHint     → FullReaderSettings (onDismissMacVoiceHint)
│   └── speakLookup                   → LookupCard (onPronounce)
│
├── useReaderPreferences()            [lib: useReaderPreferences.ts]
│   └── preferences.ttsRate
│       └── → useReadAloud (ttsRate arg)
│
├── useReadAloud()                    [lib: useReadAloud.ts]
│   ├── handleReadAloud               → Toolbar (onReadAloud)
│   │                                  → useKeyboardShortcuts (readAloud → 'r')
│   ├── handlePauseReadAloud          → Toolbar (onPauseReadAloud)
│   ├── handleResumeReadAloud         → Toolbar (onDoubleClickPause)
│   ├── handleStopReadAloud           → Toolbar (onStopReadAloud)
│   │                                  → useKeyboardShortcuts (stopReadAloud → 's')
│   ├── readAloudHidden et al.        → Toolbar (visibility flags)
│   ├── pauseReadAloudLabel           → Toolbar (button label)
│   ├── readAloudDisabled             → Toolbar (disabled prop)
│   └── rsvpWords                     → RSVPReader (words prop)
│
├── useKeyboardShortcuts()            [lib: useKeyboardShortcuts.ts]
│   ├── 'r' → readAloud.handleReadAloud
│   └── 's' → readAloud.handleStopReadAloud
│
└── Renders:
    ├── Toolbar        (chrome/Toolbar.tsx)            [TTS play/pause/stop]
    ├── FullReaderSettings (reading/ReaderControls.tsx) [voice + rate + hint]
    ├── QuickReadingPopover (reading/ReaderControls.tsx) [no TTS]
    ├── LookupCard     (lookup/LookupCard.tsx)         [pronounce button]
    └── RSVPReader     (reading/RSVPReader.tsx)         [timer-based; reads rsvpWords]
```

**Orphan component** (not wired in production):
- `lookup/VoiceHint.tsx` — standalone Mac voice hint aside; imported only in tests.

---

## 17. Test Selector Cheat-Sheet

| Selector | Element | Test usage |
|---|---|---|
| `[data-zr-read-aloud]` | Toolbar Read button | `overlay.test.ts`, `components.test.tsx` |
| `[data-zr-pause-read-aloud]` | Toolbar Pause button | `overlay.test.ts`, `components.test.tsx` |
| `[data-zr-stop-read-aloud]` | Toolbar Stop button | `overlay.test.ts`, `components.test.tsx` |
| `[data-zr-voice]` | Voice `<select>` in settings | `overlay.test.ts` |
| `[data-zr-pronounce]` | Pronounce button in `LookupCard` | `overlay.test.ts` |
| `[data-zr-dismiss-voice-hint]` | Mac hint dismiss button | `overlay.test.ts` |
| `[data-zr-sentence-index="N"]` | Sentence span (set by `HighlightManager`) | `overlay.test.ts`, `highlight.test.ts` |
| `.zr-active-sentence` (class) | Active sentence highlight | `highlight.test.ts` |
| `.zr-active-word` (class) | Active word highlight (fallback DOM path) | `highlight.test.ts` |
| `localStorage['zr.tts.voiceName']` | Selected voice persistence | `overlay.test.ts` |
| `localStorage['zr.tts.macVoiceHintDismissed']` | Mac hint dismiss persistence | `overlay.test.ts` |
| `localStorage['zr.reader.prefs']` | Reader preferences (incl. `ttsRate`) | (no direct TTS test reads this) |

---

## 18. Recommendations (ordered by leverage)

1. **Add `onerror` to `karaoke.ts`** — emits `done` on error. Prevents the
   UI-stuck state. Smallest change, biggest UX win.
2. **Add `voiceschanged` listener to `useVoiceSettings`** — fixes the
   empty-voice-list-on-first-open issue. Mirror the listener with cleanup
   in `useEffect`.
3. **Honor `reducedMotion` in `karaoke.ts`** — pass a `reducedMotion`
   boolean; skip `word-start` events when true. ADR-0023 compliance.
4. **Add `pauseReadAloud` to `READER_COMMANDS`** — wire to `'p'`
   shortcut. Closes the keyboard gap.
5. **Decide on `VoiceHint.tsx`** — delete the orphan or wire it. The
   dual-variant i18n keys (`macVoiceHint` vs `macVoiceHintShort`) suggest
   the body-level version was planned.
6. **Add pause→resume and error tests** to `karaoke.test.ts`.
7. **Consolidate voice settings into `useReaderProfile`** — single
   `localStorage` namespace, single hook, single source of truth.
8. **Decouple `rsvpWords` from `useReadAloud`** — move to `lib/text`.
9. **Add unmount cleanup** — `useEffect(() => () => karaokeRef.current?.stop(), [])`
   in both `useReadAloud` and `useVoiceSettings`.
10. **Type-narrow `speakLookup`** — replace `as unknown` cast with a
    proper type guard.

---

## Appendix A — `TTSProvider` Implementation Footprint

There is exactly **one** implementation of `TTSProvider`:
`createWebSpeechTTSProvider(speechSynthesis)`. No other adapter, no
factory switch, no DI container. Adding a cloud TTS provider would
require (a) introducing an interface beyond `TTSProvider` (the type lives
in `lib/reading/types.ts`, not in a port), (b) modifying
`useReadAloud` to accept a factory, and (c) updating the settings UI to
choose between them. This is a **deliberate** single-implementation
choice (ADR-0004) — not an oversight.

## Appendix B — Event Lifecycle Reference

| Event | Emitted by | Consumer action |
|---|---|---|
| `sentence-start` | `karaoke.ts` on `utterance.onstart` | `highlightManager.setActiveSentence(index)` |
| `sentence-end` | `karaoke.ts` on `utterance.onend` (recursive trigger) | `highlightManager.clear()` is **not** called; `speakSentence(i+1)` is |
| `word-start` | `karaoke.ts` on `utterance.onboundary` (name === 'word') | `highlightManager.setActiveWord(charIndex, charLength)` |
| `done` | `karaoke.ts` from `start()` (empty array), from `speakSentence(i >= length)`, and from `stop()` | `highlightManager.clear()` + reset UI flags |

`KaraokeEvent` has **no** `error` variant. There is no `pause` or
`resume` event. `HighlightManager.reducedMotion` is informational only.

## Appendix C — ADRs Referenced (for context)

- ADR-0004: Tech stack & extensibility (defines `TTSProvider` as a seam)
- ADR-0005: Overlay rendering & tap-word (defines `Intl.Segmenter` reuse)
- ADR-0007: Word lookup & dictionary pipeline (IPA data source)
- ADR-0008: TTS and tiered karaoke highlighting (PRIMARY)
- ADR-0011: Information architecture & onboarding (smart defaults)
- ADR-0012: Security, permissions, privacy (no permissions for TTS)
- ADR-0013: Quality, performance, resilience (offline fallback rules)
- ADR-0023: Accessibility (reduced motion + TTS as a11y aid)
- ADR-0024: Reader Profile settings architecture (TTS voice/rate)
- ADR-0026: Learning loop before comfort UI (TTS Reader Commands)
