import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/v1/catalog/voices", () =>
    HttpResponse.json({
      schema_version: "v1",
      voices: [
        {
          id: "voice.en-us",
          model_id: "pack.en-us",
          name: "English Demo",
          engine: "piper-plus",
          supported_locales: ["en-US"],
          installed: true,
          risk_class: "stock",
          governance_status: "allowed",
        },
        {
          id: "voice.vi-vn",
          model_id: "pack.vi-vn",
          name: "Vietnamese Demo",
          engine: "kokoro",
          supported_locales: ["vi-VN"],
          installed: false,
          risk_class: "reference",
          governance_status: "gated",
        },
        {
          id: "voice.fr-fr",
          model_id: "pack.fr-fr",
          name: "French Demo",
          engine: "piper-plus",
          supported_locales: ["fr-FR"],
          installed: false,
          risk_class: "stock",
          governance_status: "allowed",
        },
      ],
    }),
  ),
  http.post("/v1/models/install", () =>
    HttpResponse.json({
      schema_version: "v1",
      job_id: "job-1",
      status: "queued",
    }),
  ),
  http.get("/v1/models/install/job-1", () =>
    HttpResponse.json({
      schema_version: "v1",
      job_id: "job-1",
      status: "succeeded",
    }),
  ),
  http.get("/v1/health", () =>
    HttpResponse.json({
      schema_version: "v1",
      ready: true,
      health_status: "ok",
      total_usable_voices: 2,
    }),
  ),
  http.post(
    "/v1/audio/speech",
    () => new HttpResponse(new Uint8Array([0, 1, 2]), { status: 200 }),
  ),
];
