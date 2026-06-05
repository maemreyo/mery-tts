# ADR-0010 — Full structured error taxonomy

Source ADR: `docs/adr/ADR-0010-error-taxonomy.md`

## Goal

Replace product-critical plain strings with stable structured errors, i18n keys, fallback policy, recommended actions, and sanitized diagnostics shared by API, CLI, engines, catalog, models, and security.

## Issues

1. [Define structured error taxonomy](issues/01-define-structured-error-taxonomy.md)
2. [Add diagnostic sanitization and error factories](issues/02-add-diagnostic-sanitization-and-error-factories.md)
3. [Map domain failures to fallback policies](issues/03-map-domain-failures-to-fallback-policies.md)
