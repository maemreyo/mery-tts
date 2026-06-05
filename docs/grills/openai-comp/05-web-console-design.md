# Grill 05 — Web console design

**Parent:** `docs/grills/openai-comp/04-provider-rollout-strategy.md`  
**Status:** Q47–Q55 recommended; web console design grill closed

This grill designs the web/admin surface after:

1. P0 OpenAI-compatible blocking speech.
2. P1 raw PCM HTTP streaming.
3. Catalog/install hardening.
4. Provider rollout strategy.

The standing constraints for every decision:

- Flexible: web UI should adapt as engines/providers/catalogs grow.
- Clean: UI must not duplicate domain/install/provider logic.
- SoC: web components call API/client services; backend remains source of truth.
- Modular technically: catalog, installed voices, jobs, diagnostics, playback, and settings should be separable.
- Standalone: web console should be useful without OpenAI SDK clients.
- Scalable: design should support many voices/providers without becoming a hardcoded dashboard.
- Well-tested: component tests, API-client tests, and contract-backed mock fixtures.

---

## Decision tree

- Q47 Web console scope: **local admin console for catalog, installed voices, install jobs, diagnostics, and speech smoke tests — not a provider-specific control panel**.
- Q48 Web implementation shape: **single-page local console served by Mery first, with static bundle calling the same local `/v1` APIs**.
- Q49 Frontend stack: **Vite + React + TypeScript, TanStack Query for server state, Vitest/Testing Library/MSW for tests; avoid SSR/Next.js for local console first**.
- Q50 First web slice: **Catalog + install job tracer bullet before Dashboard, proving list -> install -> job status -> installed-state refresh lifecycle**.
- Q51 Web auth UX: **reuse existing API bearer token with a local token entry screen; memory storage by default, localStorage only as explicit opt-in**.
- Q52 Jobs UX transport: **poll install job status first; add `/v1/events` WebSocket later as progressive enhancement**.
- Q53 Try Speech UX: **WAV blocking playback first with `<audio>`; raw PCM streaming playback/download later**.
- Q54 Catalog UI scale: **table-first for desktop with search/filter/sort; compact cards only for narrow screens**.
- Q55 Web console DoD: **first milestone is done when packaged `/console`, auth, catalog install lifecycle, WAV Try Speech, diagnostics, and tests are complete; exclude streaming/marketplace/tuning/cloning UI**.

---

## Q47 — Web console scope: what should “phần web” include first?

### Recommendation

Build the web console as a **local admin console** for Mery’s runtime, not as a provider-specific control panel.

The first web scope should include:

```text
1. Dashboard / health summary
2. Catalog browser
3. Installed voices
4. Install job status
5. Voice test / speech smoke panel
6. Diagnostics
7. Basic settings links or read-only config summary
```

Do not start with a complex marketplace, provider-specific tuning UI, account system, or voice-cloning studio.

### Why this scope

After protocol, streaming, catalog/install, and provider rollout, the web UI’s job is to make the local system understandable and operable:

```text
What engines are available?
What voices can I install?
What voices are already installed?
Is an install running or failed?
Can I test a voice quickly?
Why is something unavailable?
```

That is the highest-leverage web surface. It supports local users, developers, and debugging without coupling the UI to individual provider internals.

### Core boundary

The web console should be an API client, not a second backend brain.

```text
Web UI
  -> calls /v1/health
  -> calls /v1/engines
  -> calls /v1/catalog/voices
  -> calls /v1/voices/installed
  -> calls /v1/models/install
  -> calls /v1/models/install/{jobId}
  -> calls DELETE /v1/models/{voiceId}
  -> calls /v1/diagnostics
  -> calls /v1/audio/speech for smoke tests
```

The UI must not:

```text
- infer artifact paths;
- parse catalog signatures;
- know provider download URLs as install authority;
- implement install state transitions;
- hardcode provider-specific route behavior;
- bypass VoiceRegistry or InstallService semantics.
```

### Recommended first navigation

```text
WebConsole
  Dashboard
  Catalog
  Installed Voices
  Jobs
  Diagnostics
  Try Speech
  Settings/About
```

This is intentionally operational. The web console should first answer “is my local Mery usable?” before it becomes a richer voice-management product.

### Page responsibilities

#### Dashboard

Shows:

```text
server status
loaded engines count
installed voices count
active install jobs
last diagnostic severity
quick links
```

#### Catalog

Shows flat `CatalogVoiceCard[]`:

```text
voice name
language/locale
engine
license/commercial use
size
installed state
hardware/no-card badge when available
install button
```

Install button calls `POST /v1/models/install { catalogEntryId }`.

#### Installed Voices

Shows installed/routable voices:

```text
voiceId
display name
engine
language
capabilities
status/routable
delete action
try speech action
```

Delete calls `DELETE /v1/models/{voiceId}`.

#### Jobs

Shows install job state:

```text
queued/resolving/downloading/verifying/installing/refreshing/completed/failed/cancelled
progress bytes/files
error code/message
result voiceId
```

This can poll first. WebSocket `/v1/events` integration can come later.

#### Try Speech

Simple smoke test:

```text
select installed voice
input text
response_format wav or pcm
play result in browser for wav
show raw PCM limitation until browser helper exists
```

Use `/v1/audio/speech`. Do not create a separate testing endpoint.

#### Diagnostics

Shows:

```text
engine unavailable reasons
catalog trust failures
broken voice manifests
missing artifacts
install failures
runtime gate notes
```

Diagnostics should be readable and actionable, with install hints where backend provides them.

### Web architecture recommendation

Keep web code modular around API resources:

```text
web/src/api/client.ts
web/src/api/health.ts
web/src/api/engines.ts
web/src/api/catalog.ts
web/src/api/voices.ts
web/src/api/jobs.ts
web/src/api/diagnostics.ts
web/src/api/speech.ts

web/src/features/dashboard/
web/src/features/catalog/
web/src/features/installed-voices/
web/src/features/jobs/
web/src/features/diagnostics/
web/src/features/try-speech/
```

Even if the actual repo uses another frontend structure later, the separation should remain: API client modules separate from feature components.

### Testing strategy

Minimum tests for this web scope:

```text
api-client tests
  - maps /v1/catalog/voices response to CatalogVoiceCard model
  - install request sends catalogEntryId only
  - delete request uses voiceId
  - speech request uses /v1/audio/speech

component tests
  - Catalog page renders installable voices
  - installed voice disables install button or shows installed state
  - install button starts job and links to job status
  - Jobs page renders failed job error details
  - Installed Voices page calls delete by voiceId
  - Try Speech submits selected voice and text

integration/mock tests
  - fake API fixtures cover no engines, one engine, installed voice, failed install, diagnostics warning
```

Do not require real model downloads or real TTS audio for default web tests.

### Explicit non-goals for first web slice

Do not include:

```text
full marketplace UX
remote account/login system
provider-specific advanced controls
voice cloning studio
waveform editor
browser raw PCM low-latency playback helper
multi-user permissions
cloud sync
GPU tuning UI
```

Those are later web grills.

### Decision

The first web feature should be a local Mery admin console:

```text
Dashboard + Catalog + Installed Voices + Jobs + Diagnostics + Try Speech
```

It should consume backend APIs, not duplicate backend logic. This keeps the web layer flexible, clean, SoC-preserving, modular, standalone for local operation, scalable across many providers, and well-tested with API fixtures instead of real engine dependencies.

---

## Q48 — Web implementation shape: single-page local console or separate frontend app?

### Recommendation

Start with a **single-page local console served by Mery**.

Recommended shape:

```text
GET /console
  -> serves static web bundle

GET /console/assets/*
  -> serves compiled JS/CSS/assets

Web bundle
  -> calls same local /v1 APIs
```

Do not start with a separately deployed frontend app. Mery is a local TTS helper/server; the console should be available wherever the server is running.

### Why local console first

A separate frontend app adds friction too early:

```text
separate dev server
separate hosting
separate CORS rules
separate auth assumptions
separate deploy story
more ways for local users to fail setup
```

The first web goal is operational clarity, not SaaS-style frontend independence.

Local console first gives:

```text
one process to run
one local origin
same auth/session/token model
same API base path
works offline with bundled assets
simple packaging story
```

### Clean boundary

The web console is still frontend code. Serving it from Mery does not mean mixing UI logic into domain code.

Boundary:

```text
Backend API/domain/install logic
  -> owns catalog, install jobs, artifacts, voice registry, synthesis, diagnostics

Static serving route
  -> owns only serving built frontend files

Web bundle
  -> owns UI state, views, API-client calls, optimistic/polling behavior
```

Forbidden coupling:

```text
UI reads local artifact files directly
UI parses installed manifests directly
UI computes install state transitions
UI verifies catalog signatures
UI hardcodes provider-specific install behavior
Backend route embeds page-specific business logic
```

### Route design

Recommended routes:

```text
/console              -> index.html
/console/*            -> SPA fallback to index.html, except assets
/console/assets/*     -> static assets
/v1/*                 -> existing API
```

Use `/console` instead of `/` so the API server root can remain free for docs, health redirects, or plain text server info.

Optional later redirect:

```text
GET /
  -> small landing page or redirect to /console
```

### Build/package layout

Recommended conceptual layout:

```text
web/
  package.json
  src/
  tests/
  dist/

src/mery_tts/web/
  static/        # packaged built assets copied from web/dist
```

Python packaging should include built static assets so installed Mery can serve the console without Node.js installed at runtime.

Development can still use a frontend dev server later, but production/local user mode should not require it.

### API base URL

The web bundle should default to same-origin API calls:

```text
fetch('/v1/catalog/voices')
fetch('/v1/models/install')
fetch('/v1/voices/installed')
```

Do not hardcode `localhost:8765` into the bundle. Same-origin keeps reverse proxy and non-default port setups easier.

If needed later, support configurable base path:

```text
window.__MERY_CONFIG__.apiBaseUrl
```

But first slice should stay same-origin.

### Auth handling

Reuse the existing local Mery auth model.

Do not invent separate web-console auth for the first slice.

Possible first behavior:

```text
same bearer token/cookie/session mechanism as API
console API calls include credentials/token using shared API client
unauthorized API response routes UI to token entry screen or setup hint
```

The web UI should display auth failures clearly, not bypass API security.

### Testing strategy

Minimum tests for this decision:

```text
backend/static_console_route_test.py
  - GET /console serves index.html
  - GET /console/assets/app.js serves static asset
  - SPA fallback under /console/... returns index.html
  - /v1 routes are unaffected

web/api_base_test.ts
  - API client uses same-origin /v1 paths by default
  - no hardcoded localhost URL

web/console_boot_test.tsx
  - console loads dashboard shell with mocked API
  - unauthorized API response shows auth/setup state
```

Packaging check:

```text
build includes console static assets
installed package can serve /console without Node.js runtime
```

### Future escape hatch

If Mery later needs a hosted/cloud console, this design does not block it.

Because the frontend talks to `/v1` through an API client boundary, the same UI can later run as:

```text
local static bundle served by Mery
separate dev server during development
hosted remote console with configured apiBaseUrl
```

The key is to keep API-client configuration clean and avoid backend page-specific hacks.

### Decision

Use a single-page local console served by Mery first:

```text
/console -> static SPA -> same-origin /v1 API calls
```

This keeps the web feature flexible for future hosting, cleanly separated from backend domain logic, modular in frontend/API-client structure, standalone for local users, scalable across many providers, and well-tested through static-route and mocked-API frontend tests.

---

## Q49 — Frontend stack: what should the web console use?

### Recommendation

Use **Vite + React + TypeScript** for the first web console.

Recommended stack:

```text
Vite
React
TypeScript
TanStack Query
React Router or simple route state
Vitest
Testing Library
MSW
```

Use a generated/typed API client if OpenAPI generation is already clean. If not, start with a hand-written thin typed API client and keep it isolated so it can be replaced by generated clients later.

Do **not** start with Next.js or SSR for this local console.

### Why this stack

The first web console is a small local SPA served by Mery. It needs:

```text
fast static build
simple local packaging
strong typed components
good test tooling
mocked API tests
easy same-origin /v1 calls
no server-side frontend runtime
```

Vite + React + TypeScript fits that shape. It produces static files that Python can package and serve from `/console` without needing Node.js at runtime.

### Why not Next.js

Next.js is powerful, but it adds unnecessary assumptions for this phase:

```text
SSR/server runtime
routing conventions tied to a frontend server
extra deployment model
larger build/runtime surface
more complexity for a local helper console
```

Mery already has a backend server. The first console should be a static bundle, not a second application server.

If the project later needs a hosted/cloud console, the API-client boundary can support that without starting with Next.js now.

### Server state management

Use **TanStack Query** for server state:

```text
health query
engines query
catalog voices query
installed voices query
install job query/polling
 diagnostics query
speech mutation
install mutation
delete mutation
```

Why: most UI data is backend-owned. TanStack Query gives caching, loading states, retries, invalidation, polling, and mutation handling without inventing custom global state.

Recommended invalidation examples:

```text
install mutation success -> invalidate jobs, catalog voices
job completed -> invalidate installed voices, catalog voices, engines/diagnostics if needed
delete mutation success -> invalidate installed voices, catalog voices, diagnostics
```

### Local UI state

Use component/local state for UI-only concerns:

```text
selected voice
catalog filters
search text
active tab
speech input text
expanded diagnostics row
```

Do not put backend entities into a custom global store unless there is a proven need. Backend state belongs in query cache.

### API client boundary

Recommended layout:

```text
web/src/api/http.ts
web/src/api/types.ts
web/src/api/health.ts
web/src/api/engines.ts
web/src/api/catalog.ts
web/src/api/voices.ts
web/src/api/jobs.ts
web/src/api/diagnostics.ts
web/src/api/speech.ts
```

Rules:

```text
components call feature hooks
feature hooks call API client/query functions
API client is the only place that knows raw fetch details
```

Example:

```text
CatalogPage
  -> useCatalogVoices()
  -> catalogApi.listVoices()
  -> GET /v1/catalog/voices
```

This keeps components clean and testable.

### Routing

Use simple route structure:

```text
/console
/console/catalog
/console/voices
/console/jobs
/console/diagnostics
/console/try
/console/settings
```

If React Router adds value, use it. If the first slice is tiny, route state can be simpler. The important thing is that the backend serves SPA fallback under `/console/*`.

### Styling/UI library

Do not overcommit to a heavy design system first.

Recommended first approach:

```text
CSS modules or lightweight utility CSS
small shared components: Button, Card, Badge, Table, EmptyState, ErrorState
accessible HTML defaults
```

If a component library is later needed, add it after core flows are proven. The web console should first be usable and testable, not visually overbuilt.

### Testing strategy

Minimum frontend tests:

```text
api client tests
  - uses same-origin /v1 paths
  - maps success/error responses
  - install sends catalogEntryId only
  - delete uses voiceId

query hook tests
  - catalog voices load state
  - install mutation invalidates jobs/catalog
  - job polling updates status
  - delete mutation invalidates installed voices/catalog

component tests
  - Dashboard renders health summary
  - Catalog renders voice cards and install button
  - Jobs renders progress and failed error
  - Installed Voices renders delete action
  - Try Speech submits voice/text and handles audio response

MSW integration tests
  - no engines state
  - catalog with one installable voice
  - install job completes
  - failed install shows diagnostics/actionable error
```

Default web tests must not require real Mery server, real model downloads, or real audio synthesis.

### Build/package tests

Add backend/package checks:

```text
- web build emits static dist
- package includes built console assets
- GET /console serves index.html
- /console/assets/* serves built assets
- /v1 routes remain unaffected
```

This verifies the SPA is truly standalone at runtime.

### Decision

Use:

```text
Vite + React + TypeScript
TanStack Query for backend/server state
Vitest + Testing Library + MSW for tests
static build served by Mery at /console
```

Avoid SSR/Next.js for the first local console.

This keeps the frontend flexible for future hosting, cleanly separated from backend logic, modular around API resources and features, standalone as a packaged static bundle, scalable across more console pages, and well-tested with mocked API fixtures.

---

## Q50 — First web slice: which page should be built first?

### Recommendation

Build **Catalog + install job tracer bullet** first, not Dashboard first.

First web slice:

```text
Catalog page
-> list one fake catalog voice
-> click Install
-> create install job
-> show job progress/status
-> refresh installed state when complete
```

This proves the web console’s most important interaction: driving the backend catalog/install lifecycle without duplicating backend logic.

### Why not Dashboard first

Dashboard is useful, but it is mostly read-only aggregation:

```text
health
engine count
installed voice count
active job count
latest diagnostics
```

It is easier, but less valuable as the first architecture slice. It does not prove mutations, polling, job state, invalidation, or install lifecycle UX.

Catalog install does.

### Tracer bullet flow

Recommended first flow:

```text
GET /console/catalog
  -> web calls GET /v1/catalog/voices
  -> renders CatalogVoiceCard[]

User clicks Install
  -> web calls POST /v1/models/install { catalogEntryId }
  -> receives 202 { jobId, status }

Web shows job status
  -> poll GET /v1/models/install/{jobId}
  -> render queued/resolving/downloading/verifying/installing/refreshing/completed/failed

Job completes
  -> invalidate catalog voices
  -> invalidate installed voices
  -> card shows installed=true
```

This maps directly onto the backend design from catalog/install hardening.

### UI components in first slice

Keep components small:

```text
CatalogPage
CatalogVoiceCard
InstallButton
InstallJobInlineStatus
ErrorState
EmptyState
LoadingState
```

Do not build a global dashboard, complex filters, or full navigation first unless necessary for the route shell.

### API hooks

Recommended hooks:

```typescript
useCatalogVoices()
useInstallModel()
useInstallJob(jobId, { enabled })
```

Mutation invalidation:

```text
install started
  -> show inline job state

job completed
  -> invalidate catalog voices
  -> invalidate installed voices

job failed
  -> show structured error and retry/help action
```

### Polling vs events

Use polling first.

```text
GET /v1/models/install/{jobId} every 500–1000ms while active
stop polling on completed/failed/cancelled
```

Do not require `/v1/events` WebSocket for the first web slice. WebSocket events can enhance jobs later, but polling is simpler and robust enough for local installs.

### Error UX

The first slice must handle errors cleanly:

```text
catalog load failed
install start failed
job failed
unauthorized
server offline
```

Show backend error code/message where available. Do not collapse everything to “Something went wrong.”

Example failed job state:

```text
Install failed: install.hash_mismatch
The downloaded file did not match the trusted catalog hash.
```

### Test strategy

Minimum tests for first web slice:

```text
web/catalog_page_test.tsx
  - renders loading state
  - renders empty catalog state
  - renders one catalog voice card
  - install button sends catalogEntryId
  - active job status is displayed
  - completed job invalidates/refetches catalog and shows installed state
  - failed job shows structured error

web/api/catalog_api_test.ts
  - listCatalogVoices calls /v1/catalog/voices

web/api/install_api_test.ts
  - installModel sends POST /v1/models/install with catalogEntryId only
  - getInstallJob calls /v1/models/install/{jobId}

web/msw/catalog_install_flow_test.tsx
  - MSW simulates catalog -> install -> queued -> completed -> installed card
```

Backend/static tests from Q48 still apply:

```text
GET /console/catalog -> serves SPA fallback
/v1 routes unaffected
```

### Definition of done for first web slice

First web slice is done when:

```text
1. /console/catalog loads the SPA.
2. Catalog page lists fake catalog voice from mocked or real fake backend.
3. Install button calls POST /v1/models/install with catalogEntryId.
4. UI shows install job status until terminal state.
5. Completed job updates installed state.
6. Failed job shows structured error.
7. Tests cover API client, component flow, and SPA static route.
```

### Decision

Build Catalog + install job tracer bullet first.

This keeps the web implementation flexible, cleanly API-driven, SoC-preserving, modular by feature/hooks/components, standalone with mocked fixtures, scalable to later pages, and well-tested around the most important lifecycle mutation.

---

## Q51 — Web auth UX: how should the console authenticate locally?

### Recommendation

Reuse the existing Mery API bearer token and add a **local token entry screen** in the console.

Do not create a separate web account/login system for the first web console.

Recommended flow:

```text
User opens /console
-> web app calls a lightweight /v1 endpoint such as /v1/health or /v1/engines
-> API returns 401
-> console shows “Enter Mery local token” screen
-> user enters token
-> token is stored in memory by default
-> API client sends Authorization: Bearer <token>
-> optional “remember on this device” stores token in localStorage
```

Default storage should be memory-only. Persistent browser storage should be explicit opt-in.

### Why reuse API bearer token

The console is just another API client. It should not get a special bypass around backend auth.

Clean rule:

```text
If /v1 requires auth, /console API calls require the same auth.
```

This keeps security and behavior consistent across:

```text
OpenAI SDK clients
curl users
CLI tools
web console
future desktop/native bridge
```

### Why not a separate login system

A separate login/account model is unnecessary early and creates more surface area:

- user database or account state;
- password reset/session semantics;
- separate permissions model;
- separate CSRF/session decisions;
- confusion between local token and web account.

Mery is a local helper/server first. The console should authenticate to the local API, not become an identity provider.

### Token storage policy

Recommended storage tiers:

```text
Memory only
  -> default
  -> token disappears on reload/browser close
  -> safest first behavior

localStorage opt-in
  -> user checks “remember on this device”
  -> convenience for trusted local machines
  -> clear warning that token is stored in browser storage
```

Avoid cookies/session storage until there is a deliberate CSRF/session design.

### API client boundary

Auth should live in the web API client layer, not inside every component.

Recommended modules:

```text
web/src/auth/token-store.ts
web/src/auth/AuthProvider.tsx
web/src/api/http.ts
```

Boundary:

```text
AuthProvider owns token state
http.ts attaches Authorization header
components call API hooks without manually passing token
```

Example behavior:

```typescript
headers: {
  Authorization: token ? `Bearer ${token}` : undefined,
}
```

Components should not know bearer-token formatting.

### Unauthorized behavior

Handle 401 centrally.

Recommended behavior:

```text
Any API call returns 401
  -> clear in-memory token
  -> show token entry screen or auth expired banner
  -> preserve intended route where possible
```

Do not let every page invent its own auth error UI.

### UX copy

Token entry screen should be clear and local-first:

```text
Mery requires your local API token.
This token is used only to call this Mery server.
By default it is kept in memory and forgotten when you close or reload the page.
```

Optional remember checkbox:

```text
Remember on this device
Stores the token in browser localStorage. Use only on a trusted machine.
```

### Security constraints

The web console must not:

```text
- embed a default token into the static bundle;
- bypass API auth because request is same-origin;
- log tokens to console;
- include tokens in URLs;
- store tokens persistently without explicit opt-in;
- create separate admin privileges not enforced by the backend.
```

Backend remains the source of authorization truth.

### Future escape hatch

If Mery later adds paired desktop/native auth or one-time local pairing, the console auth screen can support it behind the same AuthProvider boundary.

Future options:

```text
paste token
scan local pairing code
open native app to approve session
short-lived console session token
```

But first slice should stay simple: bearer token entry.

### Test strategy

Minimum tests for this decision:

```text
web/auth_token_store_test.ts
  - memory token is default
  - remember option writes to localStorage
  - clear removes memory and localStorage token

web/api_auth_header_test.ts
  - API client attaches Authorization: Bearer token
  - no Authorization header when token missing
  - token is not placed in query string

web/auth_ux_test.tsx
  - 401 shows token entry screen
  - entering token retries or allows API calls
  - remember checkbox persists token only when checked
  - 401 after token clears auth state

backend/console_auth_boundary_test.py
  - /console static assets can load as appropriate
  - /v1 API auth behavior is unchanged
  - console does not introduce unauthenticated privileged API route
```

### Decision

Use existing API bearer token auth for the web console:

```text
local token entry screen
memory storage by default
localStorage only with explicit “remember on this device” opt-in
central API client attaches Authorization header
```

This keeps auth flexible for future pairing, cleanly aligned with API security, modular through an AuthProvider/API-client boundary, standalone for local users, scalable to future clients, and well-tested without inventing a separate account system.

---

## Q52 — Jobs UX: polling first or WebSocket events first?

### Recommendation

Use **polling first** for install job UX. Add `/v1/events` WebSocket later as progressive enhancement.

Recommended first behavior:

```text
POST /v1/models/install
  -> returns { jobId, status }

while job is active:
  -> poll GET /v1/models/install/{jobId} every ~750ms

on terminal state:
  -> stop polling
  -> if completed: invalidate catalog voices + installed voices
  -> if failed/cancelled: show structured error/status
```

Active states:

```text
queued, resolving, downloading, verifying, installing, refreshing
```

Terminal states:

```text
completed, failed, cancelled
```

### Why polling first

Polling is simpler and more reliable for the first web slice:

```text
works with plain HTTP
simple to test deterministically
no reconnect logic
no event ordering concerns
no separate WebSocket auth path
no requirement that /v1/events is fully production-ready
```

For a local console, 500–1000ms polling is enough for install job feedback. The backend job state is authoritative, so polling aligns naturally with the durable `InstallJobStore` design.

### Why not WebSocket first

WebSocket events are useful, but they add complexity:

- connection lifecycle;
- reconnect/backoff;
- missed events;
- duplicate events;
- auth for WS connection;
- event ordering;
- state reconciliation after reconnect.

Those are worth solving later, but they should not block the first catalog/install web slice.

### Clean state model

Even when WebSocket exists, job state should come from `GET /v1/models/install/{jobId}`.

Rule:

```text
Job endpoint is authoritative.
Events are notifications.
```

That means the UI can later use WebSocket like this:

```text
receive install.job.updated event
-> invalidate/refetch job query
-> render authoritative job state
```

Do not make the frontend reconstruct job state only from events.

### TanStack Query shape

Recommended hook:

```typescript
function useInstallJob(jobId: string | null) {
  return useQuery({
    queryKey: ['install-job', jobId],
    queryFn: () => jobsApi.getJob(jobId!),
    enabled: jobId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return isActiveInstallStatus(status) ? 750 : false
    },
  })
}
```

On completion:

```text
queryClient.invalidateQueries(['catalog-voices'])
queryClient.invalidateQueries(['installed-voices'])
```

On failure:

```text
show job.error.code
show job.error.message
show details/install hint if available
```

### UX behavior

Inline job status on catalog card:

```text
Installing… queued
Installing… downloading 4.2 MB / 20 MB
Installing… verifying
Installing… refreshing
Installed
```

Failed state:

```text
Install failed: install.hash_mismatch
Details: downloaded file did not match trusted catalog hash.
Retry
```

If the user navigates away, the Jobs page can still show recent jobs from durable job store:

```text
GET /v1/models/install?recent=50   # optional future list endpoint
```

If job list endpoint does not exist in the first backend slice, the catalog page can track the just-created job locally while the backend exposes single-job lookup.

### WebSocket future path

Add WebSocket later only after polling slice works.

Future enhancement:

```text
useInstallEvents()
  -> connects to /v1/events
  -> listens for install.job.updated
  -> invalidates corresponding job query
  -> polling remains fallback
```

This gives better immediacy without making events the source of truth.

### Test strategy

Minimum tests for polling first:

```text
web/install_job_polling_test.tsx
  - starts polling while job status is queued/resolving/downloading/verifying/installing/refreshing
  - stops polling when completed
  - stops polling when failed
  - invalidates catalog voices and installed voices on completed
  - renders structured failed job error

web/jobs_api_test.ts
  - getInstallJob calls /v1/models/install/{jobId}
  - installModel returns jobId/status

web/msw_install_flow_test.tsx
  - MSW returns queued -> downloading -> completed
  - UI updates through statuses
  - final card shows installed state
```

Future WebSocket tests:

```text
web/install_events_test.tsx
  - event invalidates job query
  - reconnect falls back to polling
  - missed event is corrected by refetch
```

### Decision

Use polling first:

```text
poll GET /v1/models/install/{jobId} every ~750ms while active
```

Treat `/v1/events` as later progressive enhancement, not the first web dependency.

This keeps the jobs UX flexible, cleanly grounded in authoritative backend state, modular in hooks, standalone over HTTP, scalable to WebSocket enhancement later, and well-tested with deterministic mocked job transitions.

---

## Q53 — Try Speech page: WAV-only first or raw PCM streaming playback too?

### Recommendation

Build **blocking WAV playback first** for the Try Speech page. Add raw PCM streaming playback/download later.

First Try Speech flow:

```text
select installed voice
enter text
POST /v1/audio/speech { response_format: "wav", stream: false }
receive WAV bytes
create object URL
play with <audio>
show request duration + selected voice
```

Do not start with browser raw PCM streaming playback.

### Why WAV first

WAV playback is the simplest reliable browser path:

```text
browser understands WAV in <audio>
no custom buffering/scheduling
no AudioWorklet required
no sample-rate conversion logic in first slice
simple blob/object URL lifecycle
straightforward tests with mocked Blob response
```

The Try Speech page’s first job is to answer:

```text
Does this installed voice work?
Can I hear a sample?
What request did I send?
Did the backend return audio successfully?
```

WAV does that cleanly.

### Why not raw PCM streaming first

Raw PCM streaming is valuable for low-latency voice agents, but browser playback is not trivial.

A correct browser PCM streamer needs:

- response header parsing for sample rate/channels;
- chunk buffering;
- Web Audio scheduling;
- underrun handling;
- cancellation;
- backpressure/abort behavior;
- possibly AudioWorklet for robust playback.

A naive `fetch` stream to audio element does not work for raw PCM. A naive Web Audio loop can stutter.

So raw PCM streaming should be a later dedicated web feature, not part of the first Try Speech slice.

### Request shape

Use the OpenAI-compatible endpoint because that is the user-facing speech contract:

```json
POST /v1/audio/speech
{
  "voice": "kokoro:af_bella",
  "input": "Hello from Mery console",
  "response_format": "wav",
  "stream": false
}
```

If `model` is needed for explicit engine override, keep it advanced/optional. The normal path should rely on `voiceId` resolution.

### UI behavior

Try Speech page should show:

```text
voice selector from /v1/voices/installed
text input
Generate button
loading state
playback <audio controls>
download WAV button
request duration
error details
```

Recommended states:

```text
No installed voices
  -> show link to Catalog page

Voice unavailable
  -> show structured backend error

Synthesis failed
  -> show error code/message/details

Success
  -> show playable audio + metadata
```

### Blob lifecycle

The web client should manage object URLs carefully:

```text
on new WAV response -> URL.createObjectURL(blob)
on next generation/unmount -> URL.revokeObjectURL(previousUrl)
```

This avoids leaking browser memory during repeated tests.

### API client boundary

Recommended API function:

```typescript
async function createSpeechWav(request: {
  voice: string
  input: string
  model?: string
}): Promise<SpeechAudioResult>
```

Return:

```typescript
type SpeechAudioResult = {
  blob: Blob
  contentType: string
  durationMs: number
}
```

Keep raw `fetch`/Blob handling inside `speechApi`, not in page components.

### Streaming future path

Later web streaming feature:

```text
Try Speech streaming mode
  -> response_format=pcm
  -> stream=true
  -> parse X-Mery-Sample-Rate / X-Mery-Channels
  -> Web Audio playback helper
  -> abort/cancel button
  -> fallback download raw PCM
```

That should have its own tests and probably its own helper module:

```text
web/src/audio/pcm-stream-player.ts
```

Do not mix that complexity into the first WAV smoke path.

### Test strategy

Minimum tests for WAV Try Speech:

```text
web/try_speech_page_test.tsx
  - renders no-installed-voices state with Catalog link
  - renders installed voice selector
  - submits POST /v1/audio/speech with response_format=wav and stream=false
  - shows loading state while request is active
  - creates audio element/source on success
  - shows download button on success
  - shows backend error code/message on failure

web/speech_api_test.ts
  - createSpeechWav posts to /v1/audio/speech
  - sends voice/input/response_format wav/stream false
  - returns Blob and contentType
  - does not hardcode model when omitted

web/audio_object_url_test.ts
  - revokes previous object URL when new audio is generated
  - revokes object URL on unmount
```

Default tests should mock WAV bytes. They should not require real engine synthesis.

### Decision

Use blocking WAV playback first:

```text
/v1/audio/speech response_format=wav stream=false -> <audio controls>
```

Add raw PCM streaming playback later as a dedicated browser audio feature.

This keeps Try Speech flexible for future streaming, cleanly API-driven, modular around a speech API/audio helper boundary, standalone without Web Audio complexity, scalable toward low-latency playback later, and well-tested with mocked WAV blobs.

---

## Q54 — Catalog UI scale: cards, table, or both?

### Recommendation

Use a **table-first catalog UI** for desktop, with compact cards only for narrow/mobile screens.

Desktop default:

```text
data table
```

Narrow/mobile fallback:

```text
compact cards
```

Do not make pretty cards the primary desktop UI. As the catalog grows, users need sorting/filtering density more than visual tiles.

### Why table-first

The catalog will eventually include many voices across many providers. A card grid becomes hard to scan when users need to compare:

- language;
- engine;
- installed state;
- license/commercial-use;
- hardware requirement;
- size;
- quality tier;
- recommended use;
- install status.

A table handles this better.

The catalog’s primary job is not to look like a marketplace first. Its first job is operational selection:

```text
Find the right voice quickly.
Understand whether it can run locally.
Install it safely.
```

### Required catalog controls

Desktop catalog should include:

```text
search text
language/locale filter
engine filter
installed/not installed filter
license/commercial-use filter
hardware/no-card filter if metadata exists
sort by name/language/engine/size/status
install action
```

Minimum columns:

```text
Voice
Language
Engine
Quality
License
Hardware
Size
Status
Action
```

Optional later columns:

```text
Recommended for
Capabilities
Provider status
Last updated
```

### Row model

Each row should represent one `CatalogVoiceCard`:

```typescript
type CatalogVoiceRow = {
  catalogEntryId: string
  voiceId: string
  displayName: string
  language: string
  locale?: string
  engineId: string
  qualityTier: 'low' | 'medium' | 'high'
  license: string
  commercialUse: 'allowed' | 'restricted' | 'unknown'
  sizeBytes: number
  installed: boolean
  capabilities: string[]
  recommendedFor: string[]
}
```

The UI should not need normalized catalog internals. It consumes the flat API projection from Q30.

### Action behavior

Install action states:

```text
not installed -> Install button
install queued/running -> inline job status
installed -> Installed badge + optional Try/Delete links
failed install -> Failed state + retry action/details
```

Do not hide failures. Failed install rows should expose the job error or link to the Jobs page.

### Mobile/narrow behavior

On narrow screens, render compact cards using the same row data:

```text
Voice name
language + engine badges
license/hardware badges
size/status
primary action
```

This is a responsive representation, not a separate data model.

### Component boundary

Recommended components:

```text
CatalogPage
CatalogFilters
CatalogTable
CatalogTableRow
CatalogVoiceCardCompact
CatalogInstallAction
CatalogBadges
```

Filtering/sorting should be pure UI logic over `CatalogVoiceCard[]`. Install state remains backend-driven.

### Test strategy

Minimum tests:

```text
web/catalog_table_test.tsx
  - renders rows from CatalogVoiceCard[]
  - filters by language
  - filters by engine
  - filters installed/not installed
  - searches by voice/display name
  - sorts by size or name
  - install action sends catalogEntryId
  - installed row shows installed badge
  - failed install state shows error/action

web/catalog_responsive_test.tsx
  - desktop renders table
  - narrow viewport renders compact cards
  - both use same catalog data

web/catalog_badges_test.tsx
  - commercial_use allowed/restricted/unknown badges render correctly
  - hardware/no-card badge renders when metadata exists
```

Default tests should use API fixtures, not real catalog downloads.

### Decision

Use table-first catalog UI:

```text
Desktop -> filterable/sortable data table
Narrow -> compact cards
```

This keeps the web catalog flexible for many providers, cleanly based on flat API voice cards, modular in filters/table/actions, standalone from normalized backend internals, scalable to large catalogs, and well-tested through row/filter/action tests.

---

## Q55 — Web console DoD: when is the web part done enough?

### Recommendation

Close the first web milestone when the local console proves the full operational loop:

```text
server serves console
-> user authenticates
-> user sees catalog
-> user starts install
-> user watches job status
-> installed state updates
-> user tests speech
-> user can inspect diagnostics
```

Do not require raw PCM browser streaming, marketplace UX, provider tuning, or voice cloning UI for this milestone.

### Definition of done

The first web console milestone is done when:

```text
1. /console serves packaged SPA.
2. Auth token entry works.
3. Catalog table lists fake catalog voices.
4. Install button starts async job.
5. Job polling shows terminal state.
6. Installed state refreshes after completion.
7. Try Speech plays WAV for an installed fake or real voice.
8. Diagnostics page shows at least engine/catalog/job errors.
9. Tests cover API client, key components, MSW flows, and static serving.
```

This is enough because it proves the web console can operate Mery’s core local lifecycle without duplicating backend logic.

### Required pages for milestone 1

Required:

```text
/console/catalog
/console/voices
/console/jobs or inline job status from catalog
/console/try
/console/diagnostics
/token-entry auth screen/state
```

Dashboard can be included if cheap, but it is not the milestone anchor. The anchor is catalog install lifecycle plus speech smoke test.

### Required backend/static behavior

```text
GET /console -> index.html
GET /console/* -> SPA fallback
GET /console/assets/* -> built assets
/v1/* -> API routes unaffected
packaged install includes built assets
runtime does not require Node.js
```

The console must run from the installed Python package, not only from a frontend dev server.

### Required frontend behavior

```text
same-origin /v1 API calls
central bearer token handling
memory token by default
optional localStorage remember
catalog table search/filter/sort basics
install mutation sends catalogEntryId only
job polling stops on terminal state
completed job invalidates catalog + installed voices
failed job shows structured error
Try Speech uses wav + stream=false
object URLs are revoked
Diagnostics page renders backend diagnostic codes/messages
```

### Required tests

Minimum test set:

```text
backend/static_console_route_test.py
  - /console serves SPA
  - /console/assets serves assets
  - SPA fallback works
  - /v1 routes unaffected

web/api_client_test.ts
  - same-origin /v1 paths
  - auth header attached centrally
  - install sends catalogEntryId
  - delete uses voiceId
  - speech sends wav stream=false

web/auth_test.tsx
  - 401 shows token entry
  - token stored in memory by default
  - remember stores only when explicitly selected

web/catalog_install_flow_test.tsx
  - catalog loads fake voice
  - install starts job
  - polling shows progress
  - completed job updates installed state
  - failed job shows structured error

web/try_speech_test.tsx
  - installed voice selector renders
  - generate posts WAV request
  - audio element/download appears on success
  - object URL cleanup occurs

web/diagnostics_test.tsx
  - engine/catalog/job diagnostics render actionable messages
```

Use MSW/API fixtures. Default tests must not require real downloads, real engines, or real audio synthesis.

### Explicit non-goals

Do not include these in the first web DoD:

```text
raw PCM browser streaming playback
AudioWorklet/Web Audio low-latency player
full marketplace/storefront UX
provider-specific tuning controls
voice cloning/reference upload UI
multi-user account system
remote/cloud console hosting
GPU/backend tuning page
full provider rollout dashboard
```

Those can be later web grills once the local console lifecycle is proven.

### Closeout decision

The web console design is complete enough when milestone 1 proves:

```text
packaged local SPA
+ secure API auth reuse
+ catalog install lifecycle
+ WAV speech smoke test
+ diagnostics visibility
+ deterministic tests
```

This keeps the web work flexible for later richer UX, cleanly API-driven, SoC-preserving, modular by feature, standalone for local users, scalable across many providers, and well-tested without engine/runtime dependencies.

---

## Web console grill closeout

Final recommended sequence from Q47–Q55:

```text
Q47  Scope: local admin console, not provider-specific control panel
Q48  Implementation: static SPA served by Mery at /console
Q49  Stack: Vite + React + TypeScript + TanStack Query + Vitest/MSW
Q50  First slice: Catalog + install job tracer bullet
Q51  Auth: reuse API bearer token with local token entry
Q52  Jobs UX: polling first, WebSocket later
Q53  Try Speech: WAV blocking playback first
Q54  Catalog UI: table-first, compact cards on narrow screens
Q55  DoD: packaged console + auth + catalog install lifecycle + WAV smoke + diagnostics + tests
```

Next recommended step after all design grills: convert the design chain into implementation issues/tracer bullets, starting from OpenAI compat P0 and ending with web console milestone 1.
