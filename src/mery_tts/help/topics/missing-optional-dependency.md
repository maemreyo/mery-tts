# Missing optional dependency

Use this topic when an engine reports a missing optional package or native runtime.

1. Run `mery doctor` first; it prints a Fix plan with the exact next command when optional engine packages are missing.
2. Run `mery doctor --fix-plan` for a stable JSON repair plan that agents and scripts can inspect without changing the environment.
3. Install the matching optional extra manually, usually `uv sync --all-extras` from a repo checkout, or the narrower provider extra if your install target supports it.
4. Restart `mery serve` after dependency installation.

`mery doctor --repair --yes` only runs safe automatic local repairs. Engine package installation is a manual/network step by design, so doctor suggests the command instead of mutating the package environment implicitly.

Mery core remains usable with other installed providers while the missing optional dependency is repaired.
