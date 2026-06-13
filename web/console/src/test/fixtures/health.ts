import type {
  HealthResponse,
  HealthResponseV2,
  StorageResponse,
} from "@api/generated/client";

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

export const healthReadyV2: HealthResponseV2 = {
  schema_version: "v1",
  ready: true,
  health_status: "ok",
  total_usable_voices: 2,
  total_installed_voices: 3,
  helper_version: "1.0.0",
  health_checks: { db: "ok" },
  engines: [
    {
      engine_id: "kokoro",
      dependency_status: "available",
      installed_voice_count: 2,
      usable_voice_count: 2,
      smoked_voice_count: 2,
      smoke_passed_count: 2,
      smoke_failed_count: 0,
      status: "available",
      reason: null,
    },
    {
      engine_id: "espeak",
      dependency_status: "available",
      installed_voice_count: 1,
      usable_voice_count: 0,
      smoked_voice_count: 1,
      smoke_passed_count: 0,
      smoke_failed_count: 1,
      status: "degraded",
      reason: "Smoke test failed",
    },
  ],
};

export const storageReady: StorageResponse = {
  schema_version: "v1",
  used_bytes: 52_428_800,
  free_bytes: 1_073_741_824,
  breakdown: {
    models: 40_000_000,
    cache: 10_000_000,
    logs: 1_500_000,
    diagnostics: 928_800,
  },
  advisory: null,
};

export const storageWarn: StorageResponse = {
  schema_version: "v1",
  used_bytes: 900_000_000,
  free_bytes: 100_000_000,
  breakdown: {
    models: 800_000_000,
    cache: 80_000_000,
    logs: 15_000_000,
    diagnostics: 5_000_000,
  },
  advisory: {
    threshold_bytes: 800_000_000,
    used_bytes: 900_000_000,
    status: "warn",
    message: "Storage is running low. Consider cleaning up cache and logs.",
  },
};
