import type { DiagnosticsResponse } from "@api/generated/client";

export const diagnosticsReady: DiagnosticsResponse = {
  schema_version: "v1",
  checks: {
    runtime: "ok",
    storage: "ok",
    models: "warn",
    network: "ok",
  },
  events: [
    {
      schema_version: "v1",
      event_id: "evt-001",
      event_type: "health_check",
      occurred_at: "2026-06-13T10:00:00Z",
      severity: "info",
      source: "runtime",
      message: "Runtime is healthy",
      metadata: {},
    },
    {
      schema_version: "v1",
      event_id: "evt-002",
      event_type: "model_check",
      occurred_at: "2026-06-13T09:55:00Z",
      severity: "warning",
      source: "models",
      message: "One or more models not fully installed",
      metadata: {},
    },
  ],
};
