import type {
  InstallJobResponse,
  MeryApiClient,
  VoiceSummary,
} from "@shared/api/meryApi";

export interface VoiceViewModel {
  id: string;
  modelId: string;
  title: string;
  engine: string;
  locales: string;
  installed: boolean;
  installedLabel: string;
  governanceLabel: string;
}

export async function loadVoiceViewModels(
  api: MeryApiClient,
): Promise<VoiceViewModel[]> {
  const voices = await api.listVoices();
  return voices.map(toVoiceViewModel);
}

export function startVoiceInstall(
  api: MeryApiClient,
  modelId: string,
): Promise<InstallJobResponse> {
  return api.startInstall(modelId);
}

export function pollVoiceInstall(
  api: MeryApiClient,
  jobId: string,
): Promise<InstallJobResponse> {
  return api.getInstallJob(jobId);
}

function toVoiceViewModel(voice: VoiceSummary): VoiceViewModel {
  return {
    id: voice.id,
    modelId: voice.model_id,
    title: voice.name,
    engine: voice.engine,
    locales:
      voice.supported_locales.length > 0
        ? voice.supported_locales.join(", ")
        : "locale unknown",
    installed: voice.installed,
    installedLabel: voice.installed ? "installed" : "not installed",
    governanceLabel: `${voice.governance_status} (${voice.risk_class})`,
  };
}
