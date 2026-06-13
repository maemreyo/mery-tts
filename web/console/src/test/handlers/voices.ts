import { http, HttpResponse } from "msw";
import { voiceCatalog } from "../fixtures/voices";

export const voicesHandlers = [
  http.get("/v1/catalog/voices", () =>
    HttpResponse.json({ schema_version: "v1", voices: voiceCatalog }),
  ),
];
