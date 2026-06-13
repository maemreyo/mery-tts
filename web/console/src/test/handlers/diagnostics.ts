import { http, HttpResponse } from "msw";
import { diagnosticsReady } from "../fixtures/diagnostics";

export const diagnosticsHandlers = [
  http.get("/v1/diagnostics", () => HttpResponse.json(diagnosticsReady)),
  http.post("/v1/diagnostics", () => HttpResponse.json(diagnosticsReady)),
];
