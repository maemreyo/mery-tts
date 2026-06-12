# Readiness recovery actions

ADR-0048 P1 user-mode readiness must always answer: “what should I do next?” This table is the shared vocabulary for launcher JSON, Console companion UI, tests, and docs.

| Blocker | Primary action | User message | Command |
|---|---|---|---|
| `missing_provider_runtime` | `check_engine` | The selected speech provider is not available yet. | `mery doctor --deep` |
| `no_installed_voice` | `install_model` | No local voice is installed for synthesis. | `mery launch --action install-baseline-voice --json` |
| `port_unavailable` | `retry` | The local server is not reachable on the configured port. | `mery serve` |
| `auth_pairing_required` | `pair_client` | The client needs a valid local pairing token. | `mery pair` |
| `storage_not_writable` | `free_space` | Mery cannot write enough data to the local model storage. | `mery storage show` |
| `confirmation_required` | `confirm_update` | Model downloads require explicit user confirmation. | `mery launch --action install-baseline-voice --yes --json` |
| `network_disabled` | `contact_support` | The current policy does not allow downloading required artifacts. | Use an offline artifact or approved network path. |
| `install_failed` | `retry` | The model install job failed before the voice became usable. | `mery diagnostics-export` |
| `catalog_problem` | `retry` | The voice catalog is unavailable or invalid. | `mery catalog` |
| `smoke_failed` | `check_engine` | A previously installed voice failed readiness smoke. | `mery smoke --providers piper-plus` |

## Privacy rules

Recovery messages must not include raw synthesis text, auth tokens, private filesystem paths, or reference-audio paths. Developer detail may be attached as sanitized `detail` fields; user-mode surfaces should prefer `title`, `user_message`, `recommended_action`, and `command`.

## Launcher JSON

`mery launch --action readiness --json` includes both:

- `data.recovery_actions`: machine-readable action objects keyed by `blocker`.
- `data.next_steps`: human-readable strings derived from the same action objects.
