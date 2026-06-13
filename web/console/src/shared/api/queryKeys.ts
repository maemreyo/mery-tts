export const QUERY_KEYS = {
  health: (token: string) => ["health", token] as const,
  voices: (token: string) => ["voices", token] as const,
  installJob: (jobId: string | null, token: string) =>
    ["install-job", jobId, token] as const,
} as const;
