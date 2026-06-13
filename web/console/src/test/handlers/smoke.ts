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
  http.post("/v1/audio/speech/annotated", () => {
    return HttpResponse.json({
      audio_b64: "AAEC",
      sample_rate: 22050,
      marks_available: true,
      marks: [
        { word: "Console", start_ms: 0, end_ms: 420 },
        { word: "smoke", start_ms: 450, end_ms: 780 },
      ],
    });
  }),
];
