# Package upgrade and runtime repair

Mery P1 uses one package release channel. Stable, preview, and nightly channels are deferred.

Application upgrades are owned by the package manager that installed Mery. Mery does not self-update, does not mutate the active Python tool environment, and does not automatically roll back the application package. Mery owns state compatibility, diagnostics, catalog/model recovery, and precise repair guidance.

Use the launcher to inspect the best-effort install-method guidance:

```bash
mery launch --action readiness --json
```

Common upgrade commands:

- `uv tool`: `uv tool upgrade mery-tts-server`
- `pipx`: `pipx upgrade mery-tts-server`
- editable/dev checkout: `git pull && uv sync --all-extras`
- unknown install: use the package manager that installed Mery; common options are `uv tool upgrade mery-tts-server` or `pipx upgrade mery-tts-server`

Optional provider runtime repair is also package-manager-owned. When detection is confident, use the command family shown by readiness. When detection is unknown, choose the command for your installer instead of letting Mery rewrite the environment itself.
