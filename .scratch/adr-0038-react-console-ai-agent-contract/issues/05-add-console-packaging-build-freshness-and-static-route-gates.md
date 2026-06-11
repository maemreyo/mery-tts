# Add console packaging, build freshness, and static-route gates

Status: needs-triage

## Parent

ADR-0038 — `docs/adr/ADR-0038-react-console-ai-agent-contract.md`

## What to build

Connect the React build output to the Python package boundary and add checks proving packaged static assets are fresh, present, and served correctly without a Node.js runtime.

## Acceptance criteria

- [ ] The console build copies or emits static assets into `src/mery_tts/console` in the package-resource shape served by FastAPI.
- [ ] Built assets are committed and a check fails when `web/console` source and packaged output diverge.
- [ ] Python tests verify `/console`, `/console/setup`, `/console/assets/*`, and SPA fallback continue to work.
- [ ] Package-resource tests verify console assets are included through `importlib.resources`.
- [ ] Asset serving handles Vite-emitted JavaScript, CSS, and any required font/image/media extensions safely.
- [ ] Running the Python server and loading `/console` does not require Node.js.

## Blocked by

- `issues/04-build-react-console-shell-auth-and-voices-tracer-bullet.md`
