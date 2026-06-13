import { http, HttpResponse } from "msw";
import { smokeError, smokeOk } from "../fixtures/smoke";

export const smokeHandlers = [
  http.post("/v1/audio/speech", ({ request }) => {
    const scenario = new URL(request.url).searchParams.get("scenario");
    if (scenario === "upstream-failure") {
      return HttpResponse.json(smokeError, { status: 502 });
    }
    return new HttpResponse(new Uint8Array([0, 1, 2]), {
      status: smokeOk.ok ? 200 : 500,
      headers: { "Content-Type": "audio/wav" },
    });
  }),
];
