import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

// Placeholder generator for the ADR-0038 tracer bullet. It is intentionally
// deterministic until the FastAPI OpenAPI-to-TS generator is wired: the
// committed generated client is the source validated by check:api.
const output = resolve("src/api/generated/client.ts");
const current = await readFile(output, "utf-8");

const requiredSnippets = [
  "export interface VoiceSummary",
  "export function getVoices",
  "export function startVoiceInstall",
  "export function getInstallJob",
  "export function getHealth",
  "export function runSpeechSmoke",
];

const missing = requiredSnippets.filter((snippet) => !current.includes(snippet));
if (missing.length > 0) {
  console.error(`Generated API client template is incomplete: ${missing.join(", ")}`);
  process.exit(1);
}

await writeFile(output, current, "utf-8");
