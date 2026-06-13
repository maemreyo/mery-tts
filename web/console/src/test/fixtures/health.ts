import type { HealthResponse } from "@api/generated/client";

export const healthReady: HealthResponse = {
  schema_version: "v1",
  ready: true,
  health_status: "ok",
  total_usable_voices: 2,
};

export const healthDegraded: HealthResponse = {
  schema_version: "v1",
  ready: false,
  health_status: "degraded",
  total_usable_voices: 0,
};
