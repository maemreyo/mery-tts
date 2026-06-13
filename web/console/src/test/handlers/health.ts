import { http, HttpResponse } from "msw";
import {
  healthDegraded,
  healthReadyV2,
  storageReady,
} from "../fixtures/health";

export const healthHandlers = [
  http.get("/v1/health", ({ request }) => {
    const scenario = new URL(request.url).searchParams.get("scenario");
    if (scenario === "degraded") return HttpResponse.json(healthDegraded);
    if (scenario === "unreachable") return HttpResponse.error();
    return HttpResponse.json(healthReadyV2);
  }),
  http.get("/v1/storage", () => {
    return HttpResponse.json(storageReady);
  }),
  http.post("/v1/storage/cleanup", () => {
    return HttpResponse.json({
      schema_version: "v1",
      target: "cache",
      removed_entries: 5,
      models_protected: true,
    });
  }),
];
