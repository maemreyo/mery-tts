import { http, HttpResponse } from "msw";
import { voiceCatalog } from "../fixtures/voices";

export const voicesHandlers = [
  http.get("/v1/catalog/voices", () =>
    HttpResponse.json({ schema_version: "v1", voices: voiceCatalog }),
  ),
  http.delete("/v1/models/:modelId", ({ params }) =>
    HttpResponse.json({
      schema_version: "v1",
      model_id: params.modelId as string,
      deleted: true,
    }),
  ),
  http.get("/v1/voice-packs", () =>
    HttpResponse.json({ schema_version: "v1", voice_packs: [] }),
  ),
  http.post("/v1/voice-packs/:voicePackId/install", ({ params }) =>
    HttpResponse.json({
      schema_version: "v1",
      voice_pack_id: params.voicePackId as string,
      job_id: null,
      status: "queued",
      plan_steps: 0,
    }),
  ),
];
