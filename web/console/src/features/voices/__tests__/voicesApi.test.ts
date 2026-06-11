import type { MeryApiClient } from "@shared/api/meryApi";
import { describe, expect, it } from "vitest";
import { loadVoiceViewModels } from "../voicesApi";

describe("loadVoiceViewModels", () => {
  it("maps API voices to safe locale and governance labels", async () => {
    const api: MeryApiClient = {
      async listVoices() {
        return [
          {
            id: "voice.en-us",
            model_id: "pack.en-us",
            name: "English Demo",
            engine: "piper-plus",
            supported_locales: ["en-US"],
            installed: false,
            risk_class: "stock",
            governance_status: "allowed",
          },
        ];
      },
      async startInstall() {
        return { schema_version: "v1", job_id: "job-1", status: "queued" };
      },
      async getInstallJob() {
        return { schema_version: "v1", job_id: "job-1", status: "succeeded" };
      },
      async getHealth() {
        return {
          schema_version: "v1",
          ready: true,
          health_status: "ok",
          total_usable_voices: 1,
        };
      },
      async runSpeechSmoke() {
        return { ok: true };
      },
    };

    await expect(loadVoiceViewModels(api)).resolves.toEqual([
      {
        id: "voice.en-us",
        modelId: "pack.en-us",
        title: "English Demo",
        engine: "piper-plus",
        locales: "en-US",
        installed: false,
        installedLabel: "not installed",
        governanceLabel: "allowed (stock)",
        governanceStatus: "allowed",
        installable: true,
      },
    ]);
  });
});
