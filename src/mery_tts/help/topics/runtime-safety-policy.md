# Runtime safety policy

Mery P1 is a dependable local appliance, not a high-throughput shared TTS server.

## Safe repair

Use guided cleanup and repair commands instead of a one-click factory reset:

- `mery storage cleanup --target cache`
- `mery storage cleanup --target logs`
- `mery storage cleanup --target diagnostics`
- `mery storage repair`

Installed models are protected by default. Configuration and token reset must remain separate, strongly confirmed actions if exposed in a future UI. P1 User Mode does not expose a one-click factory reset.

## Bounded local concurrency

Mery is designed for one or a few local clients. Queue limits, backpressure, request timeouts, and structured busy/rate-limit errors protect local responsiveness and prevent state corruption.

## Cancellation and install retry

Supported speech and streaming paths use explicit cancellation. Cancellation is idempotent and releases resources. Failed or interrupted installs remain terminal failed jobs and must not become visible as successfully installed voices; retry through the launcher install action.

## CPU-first hardware

CPU is the P1 baseline. Hardware acceleration is optional metadata shown as available, unavailable, or missing-extra detail. Missing acceleration does not block P1 readiness by itself, and Mery does not download runtime dependencies automatically.

Status surfaces must include text labels and must not rely on color alone.
