import { setupServer } from "msw/node";
import { diagnosticsHandlers } from "./diagnostics";
import { healthHandlers } from "./health";
import { installHandlers } from "./install";
import { smokeHandlers } from "./smoke";
import { voicesHandlers } from "./voices";

export const server = setupServer(
  ...healthHandlers,
  ...voicesHandlers,
  ...installHandlers,
  ...smokeHandlers,
  ...diagnosticsHandlers,
);
