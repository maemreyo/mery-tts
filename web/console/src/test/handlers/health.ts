import { http, HttpResponse } from "msw";
import { healthDegraded, healthReady } from "../fixtures/health";

export const healthHandlers = [
  http.get("/v1/health", ({ request }) => {
    const scenario = new URL(request.url).searchParams.get("scenario");
    if (scenario === "degraded") return HttpResponse.json(healthDegraded);
    if (scenario === "unreachable") return HttpResponse.error();
    return HttpResponse.json(healthReady);
  }),
];
