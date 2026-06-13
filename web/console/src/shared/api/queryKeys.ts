export const QUERY_KEYS = {
  health: (token: string) => ["health", token] as const,
  voices: (token: string) => ["voices", token] as const,
  installJob: (jobId: string | null, token: string) =>
    ["install-job", jobId, token] as const,
  storage: (token: string) => ["storage", token] as const,
  diagnostics: (token: string) => ["diagnostics", token] as const,
  voicePacks: (token: string) => ["voice-packs", token] as const,
  voicePackInstallJob: (voicePackId: string, token: string) =>
    ["voice-pack-job", voicePackId, token] as const,
} as const;
