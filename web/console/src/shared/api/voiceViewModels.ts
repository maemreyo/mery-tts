import type { ConsentStatus, VoiceSummary } from "@api/generated/client";
import type { InstallJobResponse, MeryApiClient } from "./meryApi";

export interface VoiceViewModel {
  id: string;
  modelId: string;
  title: string;
  displayLabel: string;
  engine: string;
  locales: string;
  installed: boolean;
  installedLabel: string;
  governanceLabel: string;
  governanceStatus: string;
  installable: boolean;
}

function parseVoiceLabel(voiceId: string): string {
  const bare = voiceId.startsWith("catalog.")
    ? voiceId.slice("catalog.".length)
    : voiceId;
  const parts = bare.split(".");
  if (parts.length < 3) return bare;
  const [, locale, ...nameParts] = parts;
  const localeFmt = locale.replace(
    /^([a-z]{2})-([a-z]{2})$/,
    (_: string, l: string, c: string) => `${l}-${c.toUpperCase()}`,
  );
  const nameFmt = nameParts
    .flatMap((p: string) => p.split("-"))
    .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
  return nameFmt ? `${nameFmt} (${localeFmt})` : localeFmt;
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
  // Build a normalized set so we match regardless of "catalog." prefix.
  // The backend may return catalog IDs as "catalog.engine.voice" while
  // installed IDs for the same voice use the bare "engine.voice" form.
  const rawIds = installed.map((v) => v.voice_id);
  const installedIds = new Set([
    ...rawIds,
    ...rawIds.map((id) => `catalog.${id}`), // handle bare → catalog prefix
    ...rawIds.map(
      (
        id, // handle catalog prefix → bare
      ) => (id.startsWith("catalog.") ? id.slice("catalog.".length) : id),
    ),
  ]);
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
  // The backend's /v1/audio/speech and /v1/models/install accept bare IDs
  // (e.g. "piper-plus.en-us.lessac-low"), not catalog-prefixed ones
  // (e.g. "catalog.piper-plus.en-us.lessac-low").  Strip the prefix so
  // synthesis and install requests reach the correct backend handler.
  const modelId = voice.voice_id.startsWith("catalog.")
    ? voice.voice_id.slice("catalog.".length)
    : voice.voice_id;
  return {
    id: voice.voice_id,
    modelId,
    title: parseVoiceLabel(voice.voice_id),
    displayLabel: parseVoiceLabel(voice.voice_id),
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
