const TOKEN_STORAGE_KEY = "mery.console.token";
let memoryToken = "";
let catalogVoices = [];
let installedVoices = [];
let activeObjectUrl = null;

const tokenInput = document.querySelector("#token-input");
const rememberToken = document.querySelector("#remember-token");
const tokenMode = document.querySelector("#token-mode");
const catalogBody = document.querySelector("#catalog-body");
const catalogSearch = document.querySelector("#catalog-search");
const engineFilter = document.querySelector("#engine-filter");
const localeFilter = document.querySelector("#locale-filter");
const catalogSort = document.querySelector("#catalog-sort");
const jobStatus = document.querySelector("#job-status");
const voiceSelect = document.querySelector("#voice-select");
const speechText = document.querySelector("#speech-text");
const speechAudio = document.querySelector("#speech-audio");
const speechStatus = document.querySelector("#speech-status");
const voiceLocale = document.querySelector("#voice-locale");
const diagnosticsList = document.querySelector("#diagnostics-list");
const diagnosticsHistoryList = document.querySelector("#diagnostics-history-list");
const diagnosticsRetention = document.querySelector("#diagnostics-retention");
const diagnosticsRecovery = document.querySelector("#diagnostics-recovery");
const diagnosticsExportStatus = document.querySelector("#diagnostics-export-status");
const storageSummary = document.querySelector("#storage-summary");
const backendSummary = document.querySelector("#backend-summary");
const backendDetails = document.querySelector("#backend-details");
const toggleDeveloperModeButton = document.querySelector("#toggle-developer-mode");
const backendDeveloperControls = document.querySelector("#backend-developer-controls");

function setToken(token, persist) {
  memoryToken = token.trim();
  if (persist) {
    localStorage.setItem(TOKEN_STORAGE_KEY, memoryToken);
    tokenMode.textContent = "Token storage: localStorage opt-in";
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    tokenMode.textContent = "Token storage: memory only";
  }
}

function loadStoredToken() {
  const stored = localStorage.getItem(TOKEN_STORAGE_KEY) || "";
  if (stored) {
    memoryToken = stored;
    tokenInput.value = stored;
    rememberToken.checked = true;
    tokenMode.textContent = "Token storage: localStorage opt-in";
  }
}

async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (memoryToken) {
    headers.set("Authorization", `Bearer ${memoryToken}`);
  }
  if (options.json) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`/v1${path}`, {
    ...options,
    headers,
    body: options.json ? JSON.stringify(options.json) : options.body,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }
  return response;
}

async function apiJson(path, options = {}) {
  const response = await apiFetch(path, options);
  return response.json();
}

function installedVoiceIds() {
  return new Set(installedVoices.map((voice) => voice.voice_id));
}

function supportedLocales(voice) {
  return Array.isArray(voice.supported_locales) ? voice.supported_locales : [];
}

function localeLabel(voice) {
  const locales = supportedLocales(voice);
  return locales.length ? locales.join(", ") : "Unknown";
}

function governanceStatus(voice) {
  const riskClass = voice.risk_class || "stock";
  return ["reference", "cloned", "dialogue", "conversion"].includes(riskClass)
    ? `gated (${riskClass})`
    : riskClass;
}

function governanceDetails(voice) {
  const provenance = voice.provenance || "provenance unavailable";
  const trustTier = voice.trust_tier || "bundled_curated";
  const consent = voice.consent_required ? `consent ${voice.consent_status || "unknown"}` : "no consent required";
  return `${governanceStatus(voice)} · ${trustTier} · ${provenance} · ${consent}`;
}

function renderEngineFilter() {
  const selected = engineFilter.value;
  const engines = Array.from(new Set(catalogVoices.map((voice) => voice.engine_id))).sort();
  engineFilter.innerHTML = '<option value="">All engines</option>';
  for (const engine of engines) {
    const option = document.createElement("option");
    option.value = engine;
    option.textContent = engine;
    engineFilter.append(option);
  }
  engineFilter.value = selected;
}

function renderLocaleFilter() {
  const selected = localeFilter.value;
  const locales = Array.from(
    new Set(catalogVoices.flatMap((voice) => supportedLocales(voice))),
  ).sort();
  localeFilter.innerHTML = '<option value="">All locales</option>';
  for (const locale of locales) {
    const option = document.createElement("option");
    option.value = locale;
    option.textContent = locale;
    localeFilter.append(option);
  }
  localeFilter.value = selected;
}

function renderCatalog() {
  const installed = installedVoiceIds();
  const query = catalogSearch.value.trim().toLowerCase();
  const engine = engineFilter.value;
  const locale = localeFilter.value;
  const sortKey = catalogSort.value;
  const visible = catalogVoices
    .filter((voice) => !engine || voice.engine_id === engine)
    .filter((voice) => !locale || supportedLocales(voice).includes(locale))
    .filter((voice) => {
      const haystack = `${voice.display_name} ${voice.voice_id} ${voice.engine_id} ${localeLabel(voice)}`.toLowerCase();
      return !query || haystack.includes(query);
    })
    .sort((left, right) => String(left[sortKey]).localeCompare(String(right[sortKey])));

  catalogBody.innerHTML = "";
  for (const voice of visible) {
    const row = document.createElement("tr");
    const isInstalled = installed.has(voice.voice_id);
    row.innerHTML = `
      <td><strong>${voice.display_name}</strong></td>
      <td>${voice.engine_id}</td>
      <td><span class="locale-list">${localeLabel(voice)}</span></td>
      <td><code>${voice.voice_id}</code></td>
      <td><span class="status-pill ${isInstalled ? "status-installed" : "status-available"}">${isInstalled ? "installed" : "available"}</span><br><span class="governance-status">${governanceDetails(voice)}</span></td>
      <td><button type="button" data-install="${voice.voice_id}" ${isInstalled ? "disabled" : ""}>Install</button></td>
    `;
    catalogBody.append(row);
  }
}

function renderInstalledVoices() {
  voiceSelect.innerHTML = "";
  for (const voice of installedVoices) {
    const option = document.createElement("option");
    option.value = voice.voice_id;
    option.textContent = `${voice.display_name} (${voice.engine_id}; ${localeLabel(voice)})`;
    voiceSelect.append(option);
  }
  renderSelectedVoiceLocale();
  if (installedVoices.length === 0) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No installed voices";
    voiceSelect.append(option);
  }
}

function renderSelectedVoiceLocale() {
  const selected = installedVoices.find((voice) => voice.voice_id === voiceSelect.value);
  voiceLocale.textContent = selected
    ? `Selected voice locale: ${localeLabel(selected)}`
    : "Selected voice locale: none";
}

async function refreshCatalogAndVoices() {
  const [catalog, installed] = await Promise.all([
    apiJson("/catalog/voices"),
    apiJson("/voices/installed"),
  ]);
  catalogVoices = catalog.voices;
  installedVoices = installed.voices;
  renderEngineFilter();
  renderLocaleFilter();
  renderCatalog();
  renderInstalledVoices();
}

async function pollInstall(jobId) {
  let attempts = 0;
  while (attempts < 30) {
    attempts += 1;
    const status = await apiJson(`/models/install/${encodeURIComponent(jobId)}`);
    jobStatus.textContent = `Install ${jobId}: ${status.status}${status.error ? ` (${status.error})` : ""}`;
    if (["completed", "failed"].includes(status.status)) {
      await refreshCatalogAndVoices();
      return status;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Install ${jobId} did not reach terminal state`);
}

async function startInstall(catalogEntryId) {
  const voice = catalogVoices.find((entry) => entry.voice_id === catalogEntryId) || {};
  const installSummary = [
    `Source: ${voice.trust_tier || "bundled_curated"}`,
    `Size: ${voice.estimated_size_bytes || "unknown"}`,
    `License: ${voice.license_id || voice.license_scope || "bundled catalog license"}`,
    `Version: ${voice.catalog_version || "catalog-v1"}`,
    `Capability impact: ${voice.engine_id || "unknown engine"}; ${localeLabel(voice)}`,
  ].join("\n");
  const confirmed = window.confirm(
    `Install ${voice.display_name || catalogEntryId}?\n\n${installSummary}`,
  );
  if (!confirmed) {
    jobStatus.textContent = `Install cancelled for ${catalogEntryId}.`;
    return;
  }
  jobStatus.textContent = `Starting install for ${catalogEntryId}...`;
  const response = await apiJson("/models/install", {
    method: "POST",
    json: {
      schema_version: "v1",
      request_id: "console",
      model_id: catalogEntryId,
      user_confirmed: true,
    },
  });
  await pollInstall(response.job_id);
}

function renderDiagnosticsHistory(history) {
  const status = history.retention_status;
  diagnosticsRetention.textContent = `Retention: ${status.retention_days} days / ${status.max_events} events · ${status.event_count} stored${status.storage_corrupted ? " · storage recovery needed" : ""}`;
  diagnosticsHistoryList.innerHTML = "";
  for (const event of history.events.slice(-10).reverse()) {
    const row = document.createElement("li");
    row.textContent = `${event.occurred_at} · ${event.event_type} · ${event.message}`;
    diagnosticsHistoryList.append(row);
  }
}

function backendState(selection) {
  const missing = selection.missing_extras || [];
  if (missing.length) {
    return "missing-extra";
  }
  if (selection.fallback_reason) {
    return "degraded";
  }
  return selection.selected_backend === "cpu" ? "cpu-only" : "accelerated";
}

function toggleDeveloperMode() {
  const willShow = backendDeveloperControls.hidden;
  backendDeveloperControls.hidden = !willShow;
  toggleDeveloperModeButton.setAttribute("aria-expanded", String(willShow));
  toggleDeveloperModeButton.textContent = willShow ? "Hide Developer Mode" : "Show Developer Mode";
}

function renderStorageSummary(storage) {
  const breakdown = storage.breakdown || {};
  const advisory = storage.advisory || {};
  storageSummary.textContent = [
    `Storage advisory: ${advisory.status || "ok"}`,
    `models=${breakdown.models || 0} bytes`,
    `cache=${breakdown.cache || 0} bytes`,
    `logs=${breakdown.logs || 0} bytes`,
    `diagnostics=${breakdown.diagnostics || 0} bytes`,
    advisory.message || "cleanup is user-controlled",
  ].join(" · ");
}

function renderBackendSummary(health) {
  const engines = health.engines || [];
  const selections = engines
    .map((engine) => ({ engine, selection: engine.backend_selection }))
    .filter((entry) => entry.selection);
  if (!selections.length) {
    backendSummary.textContent = "Backend policy: auto; no provider backend details reported yet.";
    backendDetails.innerHTML = "";
    return;
  }

  backendSummary.textContent = selections
    .map(({ engine, selection }) => {
      const fallback = selection.fallback_reason ? `; fallback: ${selection.fallback_reason}` : "";
      return `${engine.engine_id}: ${selection.selected_backend} (${backendState(selection)}${fallback})`;
    })
    .join(" · ");

  backendDetails.innerHTML = "";
  for (const { engine, selection } of selections) {
    const row = document.createElement("div");
    const candidates = (selection.supported_backends || []).join(", ") || "none reported";
    const missing = (selection.missing_extras || []).join(", ") || "none";
    const reason = selection.fallback_reason || "selected without fallback";
    row.innerHTML = `<dt>${engine.engine_id}</dt><dd>candidate backends: ${candidates}; selected_backend: ${selection.selected_backend}; missing_extras: ${missing}; reason: ${reason}</dd>`;
    backendDetails.append(row);
  }
}

async function renderDiagnostics() {
  const [diagnostics, history, health, storage] = await Promise.all([
    apiJson("/diagnostics"),
    apiJson("/diagnostics/history"),
    apiJson("/health"),
    apiJson("/storage"),
  ]);
  diagnosticsList.innerHTML = "";
  for (const [code, message] of Object.entries(diagnostics.checks)) {
    const row = document.createElement("div");
    row.innerHTML = `<dt>${code}</dt><dd>${message}</dd>`;
    diagnosticsList.append(row);
  }
  diagnosticsRecovery.textContent = diagnostics.checks.never_run
    ? "Run diagnostics to get readiness and recovery guidance."
    : "Diagnostics checks loaded; review warnings for recovery actions.";
  renderDiagnosticsHistory(history);
  renderStorageSummary(storage);
  renderBackendSummary(health);
}

async function cleanupStorageTarget(target) {
  const result = await apiJson("/storage/cleanup", {
    method: "POST",
    json: { schema_version: "v1", request_id: "console", target },
  });
  diagnosticsExportStatus.textContent = `Storage cleanup ${result.target}: removed ${result.removed_entries}; models_protected=${result.models_protected}. cleanup is user-controlled.`;
  await renderDiagnostics();
}

async function deleteDiagnosticsHistory() {
  const result = await apiJson("/diagnostics/history", { method: "DELETE" });
  diagnosticsExportStatus.textContent = `Deleted ${result.deleted_events} diagnostics history event(s).`;
  await renderDiagnostics();
}

async function exportDiagnostics() {
  diagnosticsExportStatus.textContent = "Preparing sanitized diagnostics export...";
  const bundle = await apiJson("/diagnostics/export");
  const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `mery-diagnostics-${new Date().toISOString().replace(/[:.]/g, "-")}.json`;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  diagnosticsExportStatus.textContent = "Downloaded sanitized diagnostics export.";
}

async function playSpeech() {
  if (!voiceSelect.value) {
    speechStatus.textContent = "Install a voice before trying speech.";
    return;
  }
  speechStatus.textContent = "Requesting blocking WAV audio...";
  const response = await apiFetch("/audio/speech", {
    method: "POST",
    json: {
      model: voiceSelect.value,
      voice: voiceSelect.value,
      input: speechText.value,
      response_format: "wav",
      stream: false,
    },
  });
  const wav = await response.blob();
  if (activeObjectUrl) {
    URL.revokeObjectURL(activeObjectUrl);
  }
  activeObjectUrl = URL.createObjectURL(wav);
  speechAudio.src = activeObjectUrl;
  await speechAudio.play();
  speechStatus.textContent = "Playing WAV response; previous object URLs are revoked before reuse.";
}

async function bootstrap() {
  loadStoredToken();
  document.querySelector("#token-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    setToken(tokenInput.value, rememberToken.checked);
    await refreshCatalogAndVoices();
    await renderDiagnostics();
  });
  for (const control of [catalogSearch, engineFilter, localeFilter, catalogSort]) {
    control.addEventListener("input", renderCatalog);
  }
  voiceSelect.addEventListener("change", renderSelectedVoiceLocale);
  catalogBody.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-install]");
    if (!button) {
      return;
    }
    button.disabled = true;
    try {
      await startInstall(button.dataset.install);
    } catch (error) {
      jobStatus.textContent = error.message;
    } finally {
      renderCatalog();
    }
  });
  document.querySelector("#speech-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await playSpeech();
    } catch (error) {
      speechStatus.textContent = error.message;
    }
  });
  toggleDeveloperModeButton.addEventListener("click", toggleDeveloperMode);
  document.querySelector("#refresh-diagnostics").addEventListener("click", renderDiagnostics);
  document.querySelectorAll("[data-cleanup-target]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await cleanupStorageTarget(button.dataset.cleanupTarget);
      } catch (error) {
        diagnosticsExportStatus.textContent = error.message;
      }
    });
  });
  document.querySelector("#delete-diagnostics-history").addEventListener("click", async () => {
    try {
      await deleteDiagnosticsHistory();
    } catch (error) {
      diagnosticsExportStatus.textContent = error.message;
    }
  });
  document.querySelector("#export-diagnostics").addEventListener("click", async () => {
    try {
      await exportDiagnostics();
    } catch (error) {
      diagnosticsExportStatus.textContent = error.message;
    }
  });
  if (memoryToken) {
    await refreshCatalogAndVoices();
    await renderDiagnostics();
  }
}

window.addEventListener("beforeunload", () => {
  if (activeObjectUrl) {
    URL.revokeObjectURL(activeObjectUrl);
  }
});

bootstrap().catch((error) => {
  jobStatus.textContent = error.message;
});
