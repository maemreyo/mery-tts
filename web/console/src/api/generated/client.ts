export type VoiceRiskClass = "stock" | "cloned" | "reference" | "unknown";
export type InstallJobStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled";
export type ConsentStatus =
  | "not_required"
  | "required"
  | "granted"
  | "revoked"
  | "expired";

// Real backend field names from Python schema VoiceSummary.
// Fields: voice_id, display_name, engine_id (not id/name/engine/model_id/installed).
// `installed` is derived by cross-referencing GET /v1/voices/installed.
export interface VoiceSummary {
  voice_id: string;
  display_name: string;
  engine_id: string;
  supported_locales: string[];
  risk_class: VoiceRiskClass;
  consent_required: boolean;
  consent_status: ConsentStatus;
  trust_tier?: string;
}

export interface VoicesResponse {
  schema_version: "v1";
  voices: VoiceSummary[];
}

export interface InstalledVoicesResponse {
  schema_version: "v1";
  voices: VoiceSummary[];
}

export interface InstallVoiceRequest {
  schema_version: "v1";
  request_id: string;
  model_id: string;
  user_confirmed: true;
}

export interface InstallJobResponse {
  schema_version: "v1";
  job_id: string;
  status: InstallJobStatus;
}

export interface HealthResponse {
  schema_version: "v1";
  ready: boolean;
  health_status: string;
  total_usable_voices: number;
}

export interface SpeechSmokeRequest {
  model: string;
  voice: string;
  input: string;
  response_format: "wav";
}

export interface SpeechSmokeResponse {
  ok: boolean;
}

export interface GeneratedClientOptions {
  token: string;
  basePath?: string;
}

async function requestJson<TResponse>(
  path: string,
  { token, basePath = "/v1" }: GeneratedClientOptions,
  init: RequestInit = {},
): Promise<TResponse> {
  const response = await fetch(`${basePath}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`Mery API request failed: ${response.status}`);
  }

  return response.json() as Promise<TResponse>;
}

async function requestBinary(
  path: string,
  { token, basePath = "/v1" }: GeneratedClientOptions,
  init: RequestInit = {},
): Promise<SpeechSmokeResponse> {
  const response = await fetch(`${basePath}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "audio/wav",
      "Content-Type": "application/json",
      ...init.headers,
    },
  });
  return { ok: response.ok };
}

export function getVoices(
  options: GeneratedClientOptions,
): Promise<VoicesResponse> {
  return requestJson<VoicesResponse>("/catalog/voices", options);
}

export function getInstalledVoices(
  options: GeneratedClientOptions,
): Promise<InstalledVoicesResponse> {
  return requestJson<InstalledVoicesResponse>("/voices/installed", options);
}

export function startVoiceInstall(
  options: GeneratedClientOptions,
  request: InstallVoiceRequest,
): Promise<InstallJobResponse> {
  return requestJson<InstallJobResponse>("/models/install", options, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function getInstallJob(
  options: GeneratedClientOptions,
  jobId: string,
): Promise<InstallJobResponse> {
  return requestJson<InstallJobResponse>(`/models/install/${jobId}`, options);
}

export function getHealth(
  options: GeneratedClientOptions,
): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health", options);
}

export function runSpeechSmoke(
  options: GeneratedClientOptions,
  request: SpeechSmokeRequest,
): Promise<SpeechSmokeResponse> {
  return requestBinary("/audio/speech", options, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

// ─── Engine health (from HealthResponse.engines — already returned by /v1/health) ──
export interface EngineReadinessSummary {
  engine_id: string;
  dependency_status: "available" | "missing" | "unknown";
  installed_voice_count: number;
  usable_voice_count: number;
  smoked_voice_count: number;
  smoke_passed_count: number;
  smoke_failed_count: number;
  status: "available" | "degraded" | "unavailable";
  reason: string | null;
}

// Extend the existing HealthResponse — add new fields the backend already returns
// but were missing from the TypeScript type.
// IMPORTANT: Export a new extended type, do NOT modify the existing HealthResponse.
export interface HealthResponseV2 extends HealthResponse {
  engines: EngineReadinessSummary[];
  total_installed_voices: number;
  helper_version: string | null;
  health_checks: Record<string, string>;
}

// ─── Model delete ────────────────────────────────────────────────────────────
export interface ModelDeleteResponse {
  schema_version: "v1";
  model_id: string;
  deleted: boolean;
}

// ─── Storage ─────────────────────────────────────────────────────────────────
export interface StorageAdvisory {
  threshold_bytes: number;
  used_bytes: number;
  status: "ok" | "warn";
  message: string;
}

export interface StorageResponse {
  schema_version: "v1";
  used_bytes: number;
  free_bytes: number | null;
  breakdown: {
    models: number;
    cache: number;
    logs: number;
    diagnostics: number;
  };
  advisory: StorageAdvisory | null;
}

export type StorageCleanupTarget = "cache" | "logs" | "diagnostics";

export interface StorageCleanupResponse {
  schema_version: "v1";
  target: StorageCleanupTarget;
  removed_entries: number;
  models_protected: boolean;
}

// ─── Diagnostics ─────────────────────────────────────────────────────────────
export interface DiagnosticsEvent {
  schema_version: "v1";
  event_id: string;
  event_type: string;
  occurred_at: string;
  severity: "info" | "warning" | "error";
  source: string;
  message: string;
  metadata: Record<string, string | number | boolean>;
}

export interface DiagnosticsResponse {
  schema_version: "v1";
  checks: Record<string, string>;
  events: DiagnosticsEvent[];
}

// ─── Voice packs ─────────────────────────────────────────────────────────────
export interface VoicePackSummary {
  voice_pack_id: string;
  display_name: string;
  description: string;
  locale: string;
  supported_locales: string[];
  use_case: string;
  estimated_size_bytes: number;
  recommended: boolean;
  voices_installed: number;
  voices_total: number;
  runtimes_ready: boolean;
  status: "available" | "partial" | "missing_runtime" | "installed";
}

export interface VoicePacksResponse {
  schema_version: "v1";
  voice_packs: VoicePackSummary[];
}

export interface VoicePackInstallResponse {
  schema_version: "v1";
  voice_pack_id: string;
  job_id: string | null;
  status: string;
  plan_steps: number;
}

// ─── Annotated speech ────────────────────────────────────────────────────────
export interface SpeechMark {
  word: string;
  start_ms: number;
  end_ms: number;
}

export interface AnnotatedSpeechRequest {
  model: string;
  voice: string;
  input: string;
}

export interface AnnotatedSpeechResponse {
  audio_b64: string;
  sample_rate: number;
  marks: SpeechMark[];
  marks_available: boolean;
}

// ─── New API functions ───────────────────────────────────────────────────────

export function getHealthV2(
  options: GeneratedClientOptions,
): Promise<HealthResponseV2> {
  return requestJson<HealthResponseV2>("/health", options);
}

export function deleteVoice(
  options: GeneratedClientOptions,
  modelId: string,
): Promise<ModelDeleteResponse> {
  return requestJson<ModelDeleteResponse>(
    `/models/${encodeURIComponent(modelId)}`,
    options,
    {
      method: "DELETE",
    },
  );
}

export function getStorage(
  options: GeneratedClientOptions,
): Promise<StorageResponse> {
  return requestJson<StorageResponse>("/storage", options);
}

export function cleanupStorage(
  options: GeneratedClientOptions,
  target: StorageCleanupTarget,
): Promise<StorageCleanupResponse> {
  return requestJson<StorageCleanupResponse>("/storage/cleanup", options, {
    method: "POST",
    body: JSON.stringify({ schema_version: "v1", target }),
  });
}

export function getDiagnostics(
  options: GeneratedClientOptions,
): Promise<DiagnosticsResponse> {
  return requestJson<DiagnosticsResponse>("/diagnostics", options);
}

export function runDiagnostics(
  options: GeneratedClientOptions,
): Promise<DiagnosticsResponse> {
  return requestJson<DiagnosticsResponse>("/diagnostics", options, {
    method: "POST",
  });
}

export function getVoicePacks(
  options: GeneratedClientOptions,
): Promise<VoicePacksResponse> {
  return requestJson<VoicePacksResponse>("/voice-packs", options);
}

export function installVoicePack(
  options: GeneratedClientOptions,
  voicePackId: string,
): Promise<VoicePackInstallResponse> {
  return requestJson<VoicePackInstallResponse>(
    `/voice-packs/${encodeURIComponent(voicePackId)}/install`,
    options,
    {
      method: "POST",
      body: JSON.stringify({
        schema_version: "v1",
        voice_pack_id: voicePackId,
      }),
    },
  );
}

export function getAnnotatedSpeech(
  options: GeneratedClientOptions,
  request: AnnotatedSpeechRequest,
): Promise<AnnotatedSpeechResponse> {
  return requestJson<AnnotatedSpeechResponse>(
    "/audio/speech/annotated",
    options,
    {
      method: "POST",
      body: JSON.stringify({ ...request, response_format: "wav" }),
    },
  );
}
