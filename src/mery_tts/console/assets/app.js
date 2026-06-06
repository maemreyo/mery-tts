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
const catalogSort = document.querySelector("#catalog-sort");
const jobStatus = document.querySelector("#job-status");
const voiceSelect = document.querySelector("#voice-select");
const speechText = document.querySelector("#speech-text");
const speechAudio = document.querySelector("#speech-audio");
const speechStatus = document.querySelector("#speech-status");
const diagnosticsList = document.querySelector("#diagnostics-list");

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

function renderCatalog() {
  const installed = installedVoiceIds();
  const query = catalogSearch.value.trim().toLowerCase();
  const engine = engineFilter.value;
  const sortKey = catalogSort.value;
  const visible = catalogVoices
    .filter((voice) => !engine || voice.engine_id === engine)
    .filter((voice) => {
      const haystack = `${voice.display_name} ${voice.voice_id} ${voice.engine_id}`.toLowerCase();
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
      <td><code>${voice.voice_id}</code></td>
      <td><span class="status-pill ${isInstalled ? "status-installed" : "status-available"}">${isInstalled ? "installed" : "available"}</span></td>
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
    option.textContent = `${voice.display_name} (${voice.engine_id})`;
    voiceSelect.append(option);
  }
  if (installedVoices.length === 0) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No installed voices";
    voiceSelect.append(option);
  }
}

async function refreshCatalogAndVoices() {
  const [catalog, installed] = await Promise.all([
    apiJson("/catalog/voices"),
    apiJson("/voices/installed"),
  ]);
  catalogVoices = catalog.voices;
  installedVoices = installed.voices;
  renderEngineFilter();
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
  jobStatus.textContent = `Starting install for ${catalogEntryId}...`;
  const response = await apiJson("/models/install", {
    method: "POST",
    json: { schema_version: "v1", request_id: "console", model_id: catalogEntryId },
  });
  await pollInstall(response.job_id);
}

async function renderDiagnostics() {
  const diagnostics = await apiJson("/diagnostics");
  diagnosticsList.innerHTML = "";
  for (const [code, message] of Object.entries(diagnostics.checks)) {
    const row = document.createElement("div");
    row.innerHTML = `<dt>${code}</dt><dd>${message}</dd>`;
    diagnosticsList.append(row);
  }
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
  for (const control of [catalogSearch, engineFilter, catalogSort]) {
    control.addEventListener("input", renderCatalog);
  }
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
  document.querySelector("#refresh-diagnostics").addEventListener("click", renderDiagnostics);
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
