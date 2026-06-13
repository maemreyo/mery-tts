import {
  type AnnotatedSpeechRequest,
  type AnnotatedSpeechResponse,
  type DiagnosticsResponse,
  type GeneratedClientOptions,
  type HealthResponse,
  type HealthResponseV2,
  type InstallJobResponse,
  type ModelDeleteResponse,
  type SpeechSmokeResponse,
  type StorageCleanupResponse,
  type StorageCleanupTarget,
  type StorageResponse,
  type VoicePackInstallResponse,
  type VoicePacksResponse,
  type VoiceSummary,
  cleanupStorage,
  deleteVoice,
  getAnnotatedSpeech,
  getDiagnostics,
  getHealth,
  getHealthV2,
  getInstallJob,
  getInstalledVoices,
  getStorage,
  getVoicePacks,
  getVoices,
  installVoicePack,
  runDiagnostics,
  runSpeechSmoke,
  startVoiceInstall,
} from "@api/generated/client";

export interface MeryApiClient {
  listVoices(): Promise<VoiceSummary[]>;
  listInstalledVoices(): Promise<VoiceSummary[]>;
  startInstall(modelId: string): Promise<InstallJobResponse>;
  getInstallJob(jobId: string): Promise<InstallJobResponse>;
  getHealth(): Promise<HealthResponse>;
  runSpeechSmoke(modelId: string): Promise<SpeechSmokeResponse>;
  getHealthV2(): Promise<HealthResponseV2>;
  deleteVoice(modelId: string): Promise<ModelDeleteResponse>;
  getStorage(): Promise<StorageResponse>;
  cleanupStorage(target: StorageCleanupTarget): Promise<StorageCleanupResponse>;
  getDiagnostics(): Promise<DiagnosticsResponse>;
  runDiagnostics(): Promise<DiagnosticsResponse>;
  getVoicePacks(): Promise<VoicePacksResponse>;
  installVoicePack(voicePackId: string): Promise<VoicePackInstallResponse>;
  getAnnotatedSpeech(
    request: AnnotatedSpeechRequest,
  ): Promise<AnnotatedSpeechResponse>;
}

export function createMeryApiClient(
  options: GeneratedClientOptions,
): MeryApiClient {
  return {
    async listInstalledVoices() {
      const response = await getInstalledVoices(options);
      return response.voices;
    },
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
        model: "tts-1",
        voice: modelId,
        input: "Console smoke",
        response_format: "wav",
      });
    },
    getHealthV2() {
      return getHealthV2(options);
    },
    deleteVoice(modelId) {
      return deleteVoice(options, modelId);
    },
    getStorage() {
      return getStorage(options);
    },
    cleanupStorage(target) {
      return cleanupStorage(options, target);
    },
    getDiagnostics() {
      return getDiagnostics(options);
    },
    runDiagnostics() {
      return runDiagnostics(options);
    },
    getVoicePacks() {
      return getVoicePacks(options);
    },
    installVoicePack(voicePackId) {
      return installVoicePack(options, voicePackId);
    },
    getAnnotatedSpeech(request) {
      return getAnnotatedSpeech(options, request);
    },
  };
}

export type {
  HealthResponse,
  InstallJobResponse,
  SpeechSmokeResponse,
  VoiceSummary,
};
