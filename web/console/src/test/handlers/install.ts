import { http, HttpResponse } from "msw";
import {
  installJobCancelled,
  installJobFailed,
  installJobQueued,
  installJobRunning,
  installJobSucceeded,
} from "../fixtures/installJob";

const jobsByScenario = {
  queued: installJobQueued,
  running: installJobRunning,
  succeeded: installJobSucceeded,
  failed: installJobFailed,
  cancelled: installJobCancelled,
} as const;

export const installHandlers = [
  http.post("/v1/models/install", ({ request }) => {
    const scenario = new URL(request.url).searchParams.get("scenario");
    if (scenario === "conflict") {
      return HttpResponse.json(
        { detail: "Voice is already installed" },
        { status: 409 },
      );
    }
    return HttpResponse.json(installJobQueued);
  }),
  http.get("/v1/models/install/:jobId", ({ request }) => {
    const scenario = new URL(request.url).searchParams.get("scenario");
    return HttpResponse.json(
      jobsByScenario[scenario as keyof typeof jobsByScenario] ??
        installJobSucceeded,
    );
  }),
];
