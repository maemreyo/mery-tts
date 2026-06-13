import type {
  InstalledVoicesResponse,
  VoiceSummary,
  VoicesResponse,
} from "@api/generated/client";

/**
 * Catalog with three synthetic voices using real backend field names:
 *   voice_id, display_name, engine_id, consent_status
 *
 * English Demo — installed, consent not_required → maps to "allowed (stock)"
 * Vietnamese Demo — not installed, consent required → maps to "gated (reference)"
 * French Demo — not installed, consent not_required → installable
 */
export const voiceCatalogVoices: VoiceSummary[] = [
  {
    voice_id: "voice.en-us",
    display_name: "English Demo",
    engine_id: "piper-plus",
    supported_locales: ["en-US"],
    risk_class: "stock",
    consent_required: false,
    consent_status: "not_required",
  },
  {
    voice_id: "voice.vi-vn",
    display_name: "Vietnamese Demo",
    engine_id: "kokoro",
    supported_locales: ["vi-VN"],
    risk_class: "reference",
    consent_required: true,
    consent_status: "required",
  },
  {
    voice_id: "voice.fr-fr",
    display_name: "French Demo",
    engine_id: "piper-plus",
    supported_locales: ["fr-FR"],
    risk_class: "stock",
    consent_required: false,
    consent_status: "not_required",
  },
];

export const voiceCatalogResponse: VoicesResponse = {
  schema_version: "v1",
  voices: voiceCatalogVoices,
};

// Only English Demo is installed
export const installedVoicesResponse: InstalledVoicesResponse = {
  schema_version: "v1",
  voices: [voiceCatalogVoices[0]],
};

// Keep old export name for backward-compat with any test importing voiceCatalog
export const voiceCatalog = voiceCatalogVoices;
