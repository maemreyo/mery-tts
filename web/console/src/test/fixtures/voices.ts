import type { VoiceSummary } from "@api/generated/client";

/**
 * Catalog with three synthetic voices covering the key states exercised by
 * component tests: installed+allowed, not-installed+allowed, not-installed+gated.
 *
 * Names match what VoicesPanel.test.tsx asserts ("English Demo", etc.) so that
 * existing assertions continue to pass without modification.
 */
export const voiceCatalog: VoiceSummary[] = [
  {
    id: "voice.en-us",
    model_id: "pack.en-us",
    name: "English Demo",
    engine: "piper-plus",
    supported_locales: ["en-US"],
    installed: true,
    risk_class: "stock",
    governance_status: "allowed",
  },
  {
    id: "voice.vi-vn",
    model_id: "pack.vi-vn",
    name: "Vietnamese Demo",
    engine: "kokoro",
    supported_locales: ["vi-VN"],
    installed: false,
    risk_class: "reference",
    governance_status: "gated",
  },
  {
    id: "voice.fr-fr",
    model_id: "pack.fr-fr",
    name: "French Demo",
    engine: "piper-plus",
    supported_locales: ["fr-FR"],
    installed: false,
    risk_class: "stock",
    governance_status: "allowed",
  },
];
