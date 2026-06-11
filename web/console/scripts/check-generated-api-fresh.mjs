import { readFile } from "node:fs/promises";

const generated = await readFile("src/api/generated/client.ts", "utf-8");
const requiredSnippets = [
  "export interface VoiceSummary",
  "model_id: string",
  "supported_locales: string[]",
  "risk_class: VoiceRiskClass",
  "export function getVoices",
  "export function startVoiceInstall",
  "export function getInstallJob",
  "export function getHealth",
  "export function runSpeechSmoke",
  "basePath = \"/v1\"",
];

const missing = requiredSnippets.filter((snippet) => !generated.includes(snippet));
if (missing.length > 0) {
  console.error(`Generated API client is stale; missing: ${missing.join(", ")}`);
  process.exit(1);
}
