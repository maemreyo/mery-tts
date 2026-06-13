import type { MeryApiClient } from "@shared/api/meryApi";
import { loadVoiceViewModels } from "@shared/api/voiceViewModels";
import { describe, expect, it } from "vitest";

const stubClient: MeryApiClient = {
  async listVoices() {
    return [
      {
        voice_id: "piper-plus.en-us.demo",
        display_name: "English Demo",
        engine_id: "piper-plus",
        supported_locales: ["en-US"],
        risk_class: "stock",
        consent_required: false,
        consent_status: "not_required",
      },
    ];
  },
  async listInstalledVoices() {
    // English Demo is NOT installed in this test → installable = true
    return [];
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
  async getHealthV2() {
    return {
      schema_version: "v1",
      ready: true,
      health_status: "ok",
      total_usable_voices: 1,
      engines: [],
      total_installed_voices: 0,
      helper_version: null,
      health_checks: {},
    };
  },
  async deleteVoice() {
    return { schema_version: "v1", model_id: "", deleted: false };
  },
  async getStorage() {
    return {
      schema_version: "v1",
      used_bytes: 0,
      free_bytes: null,
      breakdown: { models: 0, cache: 0, logs: 0, diagnostics: 0 },
      advisory: null,
    };
  },
  async cleanupStorage() {
    return {
      schema_version: "v1",
      target: "cache",
      removed_entries: 0,
      models_protected: true,
    };
  },
  async getDiagnostics() {
    return { schema_version: "v1", checks: {}, events: [] };
  },
  async runDiagnostics() {
    return { schema_version: "v1", checks: {}, events: [] };
  },
  async getVoicePacks() {
    return { schema_version: "v1", voice_packs: [] };
  },
  async installVoicePack() {
    return {
      schema_version: "v1",
      voice_pack_id: "",
      job_id: null,
      status: "queued",
      plan_steps: 0,
    };
  },
  async getAnnotatedSpeech() {
    return {
      audio_b64: "",
      sample_rate: 22050,
      marks: [],
      marks_available: false,
    };
  },
};

describe("loadVoiceViewModels", () => {
  it("maps API voices to safe locale and governance labels", async () => {
    await expect(loadVoiceViewModels(stubClient)).resolves.toEqual([
      {
        id: "piper-plus.en-us.demo",
        modelId: "piper-plus.en-us.demo", // voice_id is used as modelId
        title: "Demo (en-US)",
        displayLabel: "Demo (en-US)",
        engine: "piper-plus",
        locales: "en-US",
        installed: false, // not in installedVoices above
        installedLabel: "not installed",
        governanceLabel: "allowed (stock)", // not_required → "allowed"
        governanceStatus: "allowed",
        installable: true,
      },
    ]);
  });

  it("marks voices that appear in installed list as installed", async () => {
    const installedClient: MeryApiClient = {
      ...stubClient,
      async listInstalledVoices() {
        return [
          {
            voice_id: "piper-plus.en-us.demo",
            display_name: "English Demo",
            engine_id: "piper-plus",
            supported_locales: ["en-US"],
            risk_class: "stock",
            consent_required: false,
            consent_status: "not_required",
          },
        ];
      },
    };
    const vms = await loadVoiceViewModels(installedClient);
    expect(vms[0].installed).toBe(true);
    expect(vms[0].installedLabel).toBe("installed");
    expect(vms[0].installable).toBe(false);
  });
});
