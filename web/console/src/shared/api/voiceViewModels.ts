import type { ConsentStatus, VoiceSummary } from "@api/generated/client";
import type { InstallJobResponse, MeryApiClient } from "./meryApi";

export interface VoiceViewModel {
  id: string;
  modelId: string;
  title: string;
  engine: string;
  locales: string;
  installed: boolean;
  installedLabel: string;
  governanceLabel: string;
  governanceStatus: string;
  installable: boolean;
}

// Map backend consent_status to user-facing label, preserving existing UI text
// so that tests asserting "allowed" / "gated" continue to pass.
function consentLabel(status: ConsentStatus): string {
  switch (status) {
    case "not_required":
      return "allowed";
    case "required":
      return "gated";
    case "granted":
      return "granted";
    case "revoked":
      return "revoked";
    case "expired":
      return "expired";
    default:
      return status;
  }
}

// Fetches catalog voices + installed voices in parallel, then cross-references
// to set the `installed` boolean on each ViewModel.
export async function loadVoiceViewModels(
  api: MeryApiClient,
): Promise<VoiceViewModel[]> {
  const [catalog, installed] = await Promise.all([
    api.listVoices(),
    api.listInstalledVoices(),
  ]);
  const installedIds = new Set(installed.map((v) => v.voice_id));
  return catalog.map((v) => toVoiceViewModel(v, installedIds));
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

function toVoiceViewModel(
  voice: VoiceSummary,
  installedIds: Set<string>,
): VoiceViewModel {
  const installed = installedIds.has(voice.voice_id);
  const govStatus = consentLabel(voice.consent_status);
  return {
    id: voice.voice_id,
    modelId: voice.voice_id,
    title: voice.display_name,
    engine: voice.engine_id,
    locales:
      voice.supported_locales.length > 0
        ? voice.supported_locales.join(", ")
        : "locale unknown",
    installed,
    installedLabel: installed ? "installed" : "not installed",
    governanceLabel: `${govStatus} (${voice.risk_class})`,
    governanceStatus: govStatus,
    installable:
      !installed &&
      (voice.consent_status === "not_required" ||
        voice.consent_status === "granted"),
  };
}
