export type VoiceRiskClass = "stock" | "cloned" | "reference" | "unknown";
export type InstallJobStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled";

export interface VoiceSummary {
  id: string;
  name: string;
  engine: string;
  model_id: string;
  supported_locales: string[];
  installed: boolean;
  risk_class: VoiceRiskClass;
  governance_status: string;
}

export interface VoicesResponse {
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
