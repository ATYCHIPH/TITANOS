const STORAGE_KEY = "titanos_product_state_v1";

export const workspaceModes = [
  { id: "universal", label: "Universal", useCase: "All-purpose work", tools: ["agent", "tasks", "files", "browser", "notes", "automations", "integrations", "approvals"] },
  { id: "coding", label: "Coding", useCase: "Repos, tests, deployments", tools: ["agent", "files", "code", "terminal", "git", "diffs", "tests"] },
  { id: "business", label: "Business", useCase: "Operations and approvals", tools: ["agent", "tasks", "workflows", "reports", "approvals", "crm"] },
  { id: "content", label: "Content", useCase: "Writing and campaigns", tools: ["agent", "editor", "brand", "calendar", "assets", "publishing"] },
  { id: "research", label: "Research", useCase: "Sources and reports", tools: ["agent", "browser", "sources", "citations", "notes", "documents"] },
  { id: "daily", label: "Daily Workflow", useCase: "Email, calendar, routines", tools: ["agent", "calendar", "email", "reminders", "routines", "automations"] },
  { id: "data", label: "Data", useCase: "Sheets, charts, insights", tools: ["agent", "spreadsheets", "charts", "imports", "insights"] },
  { id: "sales", label: "Sales/Support", useCase: "Leads, tickets, follow-ups", tools: ["agent", "customers", "pipeline", "tickets", "followups"] },
  { id: "custom", label: "Custom", useCase: "Choose your own workspace", tools: ["agent", "tasks", "files"] },
];

export const technicalLevels = {
  simple: {
    label: "Simple",
    hiddenTools: ["terminal", "git", "diffs", "tests", "logs", "providerAdvanced"],
  },
  standard: {
    label: "Standard",
    hiddenTools: ["terminal", "git", "diffs"],
  },
  power: {
    label: "Power User",
    hiddenTools: [],
  },
  developer: {
    label: "Developer",
    hiddenTools: [],
  },
};

export const providers = [
  { id: "openai", label: "OpenAI", fields: ["apiKey", "model"], defaultModel: "gpt-5.2" },
  { id: "anthropic", label: "Anthropic", fields: ["apiKey", "model"], defaultModel: "claude-sonnet" },
  { id: "gemini", label: "Google/Gemini", fields: ["apiKey", "model"], defaultModel: "gemini-pro" },
  { id: "groq", label: "Groq", fields: ["apiKey", "model"], defaultModel: "llama-3.3" },
  { id: "local", label: "Local endpoint", fields: ["baseUrl", "model"], defaultModel: "local-model" },
  { id: "custom", label: "Custom provider", fields: ["baseUrl", "apiKey", "model"], defaultModel: "custom-model" },
];

export function createInitialState() {
  return {
    auth: {
      session: null,
      verified: false,
      resetRequested: false,
    },
    onboarding: {
      complete: false,
      step: 0,
    },
    preferences: {
      workspaceMode: "universal",
      technicalLevel: "standard",
      visibleTools: ["agent", "tasks", "files", "browser", "notes", "automations", "integrations", "approvals"],
      theme: "dark",
      sidebarCollapsed: false,
      customLayout: ["agent", "tasks", "files"],
      currentRoute: "workspace",
    },
    providers: {},
    agent: {
      conversation: [
        {
          speaker: "TITANOS",
          text: "Welcome to the Universal Workspace. Ask for coding, business, content, research, daily workflow, data, sales, or support work.",
          time: nowTime(),
        },
      ],
      currentRun: null,
      history: [],
      approvals: [],
    },
    activity: [
      { type: "system", text: "Product workspace initialized", time: nowTime() },
    ],
  };
}

export function loadState() {
  const fresh = createInitialState();
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    if (!saved) return fresh;
    return mergeState(fresh, saved);
  } catch {
    return fresh;
  }
}

export function saveState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function resetProductState() {
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem("titanos_token");
  localStorage.removeItem("titanos_session_id");
}

export function mockAuthLogin(email) {
  const normalized = email.trim().toLowerCase();
  if (!normalized.includes("@")) throw new Error("Use a valid email address.");
  const token = btoa(`${normalized}:${Date.now()}`);
  localStorage.setItem("titanos_token", token);
  return {
    email: normalized,
    name: normalized.split("@")[0] || "operator",
    token,
    createdAt: new Date().toISOString(),
  };
}

export function maskSecret(value) {
  if (!value) return "Not saved";
  const clean = String(value);
  if (clean.length <= 8) return "••••••";
  return `${clean.slice(0, 3)}••••${clean.slice(-4)}`;
}

export async function testProviderConnection(providerId, config) {
  await delay(550);
  if (!config) throw new Error("Provider configuration is missing.");
  const provider = providers.find((item) => item.id === providerId);
  const required = provider?.fields || [];
  const missing = required.filter((field) => !String(config[field] || "").trim());
  if (missing.length) throw new Error(`Missing ${missing.join(", ")}.`);
  if (config.apiKey && String(config.apiKey).length < 8) throw new Error("API key is too short.");
  if (config.baseUrl && !/^https?:\/\/|^localhost|^127\.0\.0\.1/.test(config.baseUrl)) {
    throw new Error("Base URL must be http(s), localhost, or 127.0.0.1.");
  }
  return { ok: true, checkedAt: new Date().toISOString() };
}

export function classifyTask(text) {
  const value = text.toLowerCase();
  const rules = [
    ["coding", ["repo", "bug", "code", "deploy", "test", "terminal", "git", "landing page"]],
    ["daily", ["email", "calendar", "meeting", "reminder", "tomorrow", "today"]],
    ["research", ["research", "competitor", "source", "citation", "report"]],
    ["content", ["content", "post", "brand", "campaign", "proposal", "write"]],
    ["data", ["spreadsheet", "chart", "data", "csv", "analyze"]],
    ["sales", ["lead", "customer", "ticket", "follow up", "crm", "support"]],
    ["business", ["invoice", "workflow", "approval", "operation", "business"]],
  ];
  const match = rules.find(([, words]) => words.some((word) => containsTerm(value, word)));
  return match ? match[0] : "general";
}

export function buildAgentRun(text, technicalLevel) {
  const category = classifyTask(text);
  const sensitive = detectSensitiveAction(text);
  const selectedTools = toolsForCategory(category, technicalLevel);
  const plan = plansForCategory(category);
  const steps = plan.map((item, index) => ({
    id: `step-${Date.now()}-${index}`,
    label: item,
    status: index === 0 ? "running" : "queued",
  }));
  return {
    id: `run-${Date.now()}`,
    prompt: text,
    category,
    selectedTools,
    plan,
    steps,
    sensitive,
    status: sensitive ? "needs_approval" : "running",
    result: "",
    suggestedNextActions: [],
    startedAt: nowTime(),
  };
}

export function completeAgentRun(run) {
  const completedSteps = run.steps.map((step) => ({ ...step, status: "done" }));
  return {
    ...run,
    steps: completedSteps,
    status: "completed",
    result: resultForCategory(run.category),
    suggestedNextActions: nextActionsForCategory(run.category),
  };
}

export function detectSensitiveAction(text) {
  const value = text.toLowerCase();
  const actions = [
    "send email",
    "delete",
    "run command",
    "purchase",
    "publish",
    "change api key",
    "deploy",
    "invite",
    "export private",
  ];
  return actions.find((action) => value.includes(action)) || "";
}

export function nowTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function plansForCategory(category) {
  const shared = {
    coding: ["Inspect repository context", "Identify files and risks", "Apply focused change", "Run verification", "Prepare summary"],
    business: ["Map workflow objective", "Collect required inputs", "Draft operational plan", "Queue approvals", "Create report"],
    content: ["Extract audience and goal", "Build content angle", "Draft deliverable", "Check brand voice", "Prepare publishing checklist"],
    research: ["Define research question", "Gather source list", "Compare findings", "Build cited summary", "Suggest next questions"],
    daily: ["Check schedule and inbox context", "Prioritize actions", "Create task list", "Flag approvals", "Summarize day plan"],
    data: ["Inspect dataset shape", "Validate fields", "Compute insights", "Prepare chart summary", "List risks"],
    sales: ["Review contacts or tickets", "Prioritize follow-ups", "Draft response plan", "Queue outbound approvals", "Update pipeline summary"],
    general: ["Understand request", "Select useful tools", "Create execution plan", "Run workspace action", "Return result"],
  };
  return shared[category] || shared.general;
}

function resultForCategory(category) {
  const results = {
    coding: "Coding run staged: files, verification, Git, and deployment tools are ready for the implementation lane.",
    business: "Business workflow staged with approvals, reports, and operational tasks ready to review.",
    content: "Content plan generated with draft structure, brand checks, and publishing actions.",
    research: "Research workspace prepared with source tracking, notes, citations, and report structure.",
    daily: "Daily workflow organized into priorities, reminders, and follow-up actions.",
    data: "Data analysis plan prepared with validation, insights, and chart-ready outputs.",
    sales: "Sales/support workflow prepared with follow-ups, tickets, and pipeline actions.",
    general: "Universal agent plan completed. The workspace adapted the tools for this request.",
  };
  return results[category] || results.general;
}

function nextActionsForCategory(category) {
  const next = {
    coding: ["Open file explorer", "Run tests", "Create deployment checklist"],
    business: ["Review approval queue", "Export report", "Assign owner"],
    content: ["Open editor", "Schedule publish date", "Attach brand assets"],
    research: ["Add source", "Create citation note", "Export summary"],
    daily: ["Create reminders", "Open calendar", "Review inbox"],
    data: ["Import spreadsheet", "Create chart", "Export insights"],
    sales: ["Draft follow-up", "Update lead stage", "Open tickets"],
    general: ["Save to memory", "Create task", "Change workspace"],
  };
  return next[category] || next.general;
}

function toolsForCategory(category, technicalLevel) {
  const mode = workspaceModes.find((item) => item.id === category) || workspaceModes[0];
  const hidden = technicalLevels[technicalLevel]?.hiddenTools || [];
  return mode.tools.filter((tool) => !hidden.includes(tool));
}

function mergeState(base, saved) {
  return {
    ...base,
    ...saved,
    auth: { ...base.auth, ...(saved.auth || {}) },
    onboarding: { ...base.onboarding, ...(saved.onboarding || {}) },
    preferences: { ...base.preferences, ...(saved.preferences || {}) },
    providers: { ...base.providers, ...(saved.providers || {}) },
    agent: { ...base.agent, ...(saved.agent || {}) },
    activity: saved.activity || base.activity,
  };
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function containsTerm(value, term) {
  const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = term.includes(" ")
    ? new RegExp(`(^|\\W)${escaped}(\\W|$)`, "i")
    : new RegExp(`\\b${escaped}\\b`, "i");
  return pattern.test(value);
}
