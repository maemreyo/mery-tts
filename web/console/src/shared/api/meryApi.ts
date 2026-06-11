import {
  type GeneratedClientOptions,
  type HealthResponse,
  type InstallJobResponse,
  type SpeechSmokeResponse,
  type VoiceSummary,
  getHealth,
  getInstallJob,
  getVoices,
  runSpeechSmoke,
  startVoiceInstall,
} from "@api/generated/client";

export interface MeryApiClient {
  listVoices(): Promise<VoiceSummary[]>;
  startInstall(modelId: string): Promise<InstallJobResponse>;
  getInstallJob(jobId: string): Promise<InstallJobResponse>;
  getHealth(): Promise<HealthResponse>;
  runSpeechSmoke(modelId: string): Promise<SpeechSmokeResponse>;
}

export function createMeryApiClient(
  options: GeneratedClientOptions,
): MeryApiClient {
  return {
    async listVoices() {
      const response = await getVoices(options);
      return response.voices;
    },
    startInstall(modelId) {
      return startVoiceInstall(options, {
        schema_version: "v1",
        request_id: `console-${modelId}`,
        model_id: modelId,
        user_confirmed: true,
      });
    },
    getInstallJob(jobId) {
      return getInstallJob(options, jobId);
    },
    getHealth() {
      return getHealth(options);
    },
    runSpeechSmoke(modelId) {
      return runSpeechSmoke(options, {
        model: modelId,
        input: "Console smoke",
        response_format: "wav",
      });
    },
  };
}

export type {
  HealthResponse,
  InstallJobResponse,
  SpeechSmokeResponse,
  VoiceSummary,
};
