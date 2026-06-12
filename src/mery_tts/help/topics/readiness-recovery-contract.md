# Readiness and recovery action contract

Use launcher readiness when a client or support workflow needs a machine-readable setup summary:

```bash
mery launch --action readiness --json
```

The `capability_readiness` object is the stable P1 summary for launcher, Console, generic `/v1` clients, local help, and support bundles. It includes version layers, auth state, installed/catalog locales, provider runtime availability, OpenAI-compatible speech support, streaming support, storage advisory, blocking readiness failures, and recovery actions.

Recovery actions are user-facing and stable-additive. Render `title`, `user_message`, and optional `command` for setup guidance. Treat lower-level error codes as developer detail and ignore unknown additive fields or blockers you do not recognize.

Mery does not add Zam Reader-only backend behavior; Zam Reader is a reference client for the same generic `/v1` contract.
