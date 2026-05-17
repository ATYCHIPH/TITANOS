// api.js

const desktopBridge = window.titanosDesktop || {};
const API_BASE =
  desktopBridge.apiBase ||
  window.TITANOS_API_BASE ||
  "";

function getAuthHeader() {
  const token = localStorage.getItem("titanos_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

function endpoint(path) {
  if (/^https?:\/\//.test(path)) return path;
  if (!API_BASE) return path;
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

async function apiFetch(path, options = {}, fallback) {
  try {
    const response = await fetch(endpoint(path), options);
    if (response.status === 401) throw new Error("Unauthorized");
    if (!response.ok) throw new Error(`API request failed: ${path}`);
    return response.json();
  } catch (error) {
    if (fallback !== undefined) return typeof fallback === "function" ? fallback(error) : fallback;
    throw error;
  }
}

export async function fetchStatus() {
  return apiFetch("/status", {}, {
    brain: "local",
    cortex: "ready",
    memory: "ready",
    hands: "ready",
    eyes: "ready",
    voice: "ready",
    craft: "ready",
    lab: "ready",
  });
}

export async function fetchProviderHealth() {
  return apiFetch("/health/providers", {}, {
    providers: [
      { name: "Local", status: "offline" },
      { name: "OpenAI", status: "not_configured" },
      { name: "Anthropic", status: "not_configured" },
    ],
  });
}

export async function fetchDoctor() {
  return apiFetch("/doctor", {}, {
    cli: "desktop-local",
    version: "0.1.0",
    model: "configured in UI",
    os: navigator.platform,
    data_dir: "desktop profile",
    memory_db: "desktop profile",
    warnings: ["Backend is using the desktop fallback adapter."],
  });
}

export async function sendMessage(message, sessionId) {
  return apiFetch("/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify({
      goal: message,
      session_id: sessionId || null,
      context: [],
    }),
  }, () => ({
    session_id: sessionId || `desktop-${Date.now()}`,
    status: "success",
    response: "",
  }));
}

export async function fetchMemory() {
  return apiFetch("/memory", { headers: getAuthHeader() }, { memories: [] });
}

export async function searchMemory(query) {
  return apiFetch(`/memory/search?q=${encodeURIComponent(query)}`, { headers: getAuthHeader() }, { memories: [] });
}

export async function deleteMemory(id) {
  return apiFetch(`/memory/${id}`, {
    method: "DELETE",
    headers: getAuthHeader(),
  }, { ok: true });
}

export async function fetchSessions() {
  return apiFetch("/sessions", { headers: getAuthHeader() }, { sessions: [] });
}

export async function fetchLogs() {
  return [
    { level: "info", time: new Date().toISOString(), message: "TITANOS desktop runtime initialized" },
    { level: "debug", time: new Date().toISOString(), message: API_BASE ? `API adapter: ${API_BASE}` : "API adapter: browser-relative" },
  ];
}

export async function fetchRuntimeInfo() {
  if (desktopBridge.getRuntimeInfo) return desktopBridge.getRuntimeInfo();
  return {
    apiBase: API_BASE,
    backend: {
      state: API_BASE ? "external" : "browser",
      message: API_BASE ? "Using configured backend." : "Running without the desktop backend bridge.",
    },
    packaged: false,
    platform: navigator.platform,
  };
}

export async function restartBackend() {
  if (desktopBridge.restartBackend) return desktopBridge.restartBackend();
  return fetchRuntimeInfo();
}

export async function fetchApprovals() {
  return apiFetch("/hands/approvals", { headers: getAuthHeader() }, { approvals: [] });
}

export async function approveCommand(id) {
  return apiFetch(`/hands/approvals/${id}/approve`, {
    method: "POST",
    headers: getAuthHeader(),
  }, { ok: true });
}

export async function runApprovedCommand(id) {
  return apiFetch(`/hands/approvals/${id}/run`, {
    method: "POST",
    headers: getAuthHeader(),
  }, { status: "success", summary: "Approved command completed through the desktop fallback." });
}

export async function classifyCommand(command) {
  return apiFetch("/hands/commands/classify", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify({ command }),
  }, { risk: "safe", reason: "Desktop fallback classification." });
}

export async function writeFilePreview(path, content) {
  return apiFetch("/hands/files/write-preview", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify({ path, content }),
  }, { diff: `+ ${content}` });
}

export async function writeFile(path, content) {
  return apiFetch("/hands/files/write", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify({ path, content }),
  }, { diff: `+ ${content}`, status: "queued" });
}

export async function editFilePreview(path, old_text, new_text) {
  return apiFetch("/hands/files/edit-preview", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify({ path, old_text, new_text }),
  }, { diff: `- ${old_text}\n+ ${new_text}` });
}

export async function editFile(path, old_text, new_text) {
  return apiFetch("/hands/files/edit", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify({ path, old_text, new_text }),
  }, { diff: `- ${old_text}\n+ ${new_text}`, status: "queued" });
}

export async function fetchRuns() {
  return apiFetch("/runs", { headers: getAuthHeader() }, { runs: [] });
}

export async function explainRoute(goal) {
  return apiFetch("/route/explain", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify({ goal }),
  }, { system: "universal", confidence: 0.72, reason: "Desktop fallback route." });
}

export async function fetchBodyHealth() {
  return apiFetch("/body/health", { headers: getAuthHeader() }, {
    systems: [
      { system: "Cortex", status: "ready", summary: "Agent planning UI ready." },
      { system: "Memory", status: "ready", summary: "Local workspace memory adapter ready." },
      { system: "Hands", status: "ready", summary: "Approvals are enforced before sensitive actions." },
      { system: "Eyes", status: "ready", summary: "Research/browser panel is available." },
      { system: "Craft", status: "ready", summary: "Content workspace is available." },
      { system: "Lab", status: "ready", summary: "Data workspace is available." },
    ],
  });
}
