import {
  buildAgentRun,
  completeAgentRun,
  createInitialState,
  maskSecret,
  mockAuthLogin,
  nowTime,
  providers,
  resetProductState,
  saveState,
  loadState,
  technicalLevels,
  testProviderConnection,
  workspaceModes,
} from "./workspace-services.js";
import {
  fetchApprovals,
  fetchBodyHealth,
  fetchDoctor,
  fetchMemory,
  fetchProviderHealth,
  fetchRuns,
  sendMessage,
} from "./api.js";

let state = loadState();
const app = document.querySelector("#app");

document.addEventListener("DOMContentLoaded", () => {
  render();
  hydrateBackendSignals();
});

function setState(updater) {
  state = typeof updater === "function" ? updater(structuredClone(state)) : updater;
  saveState(state);
  render();
}

function render() {
  document.documentElement.dataset.theme = state.preferences.theme;
  if (!state.auth.session) {
    renderAuth();
    return;
  }
  if (!state.onboarding.complete) {
    renderOnboarding();
    return;
  }
  renderWorkspace();
}

function renderAuth() {
  app.innerHTML = `
    <main class="auth-layout">
      <section class="auth-brand" aria-label="TITANOS overview">
        <div class="logo-lockup large">
          <span class="logo-mark" aria-hidden="true">T</span>
          <div>
            <b>TITANOS</b>
            <small>Universal Agent Workspace</small>
          </div>
        </div>
        <h1>TITANOS /one</h1>
        <p>One universal agent for coding, business, content, research, daily workflow, data, sales, and support.</p>
        <div class="auth-proof">
          <span>Protected routes</span>
          <span>Mock-local auth adapter</span>
          <span>Provider setup in UI</span>
        </div>
      </section>
      <section class="auth-card" aria-label="Authentication">
        <div class="auth-tabs" role="tablist">
          <button class="auth-tab active" data-auth-view="login" type="button">Login</button>
          <button class="auth-tab" data-auth-view="signup" type="button">Signup</button>
          <button class="auth-tab" data-auth-view="recover" type="button">Recover</button>
        </div>
        <div id="auth-panel"></div>
      </section>
    </main>
  `;
  bindAuthTabs();
  renderAuthPanel("login");
}

function bindAuthTabs() {
  document.querySelectorAll("[data-auth-view]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-auth-view]").forEach((tab) => tab.classList.remove("active"));
      button.classList.add("active");
      renderAuthPanel(button.dataset.authView);
    });
  });
}

function renderAuthPanel(view) {
  const panel = document.querySelector("#auth-panel");
  const copy = {
    login: ["Welcome back", "Continue to your workspace", "Log in"],
    signup: ["Create account", "Start with the Universal Workspace", "Create account"],
    recover: ["Reset access", "Request a password reset link", "Send reset link"],
  }[view];
  panel.innerHTML = `
    <form class="form-stack" id="auth-form" novalidate>
      <div>
        <h2>${copy[0]}</h2>
        <p>${copy[1]}</p>
      </div>
      <label>Email
        <input id="auth-email" type="text" inputmode="email" required autocomplete="email" placeholder="you@company.com" />
      </label>
      ${view !== "recover" ? `
        <label>Password
          <input id="auth-password" type="password" required autocomplete="${view === "login" ? "current-password" : "new-password"}" placeholder="Minimum 8 characters" />
        </label>
      ` : ""}
      <p class="form-error" id="auth-error" role="alert"></p>
      <button class="primary-action" type="submit">${copy[2]}</button>
      <button class="ghost-action" id="verify-demo" type="button">Simulate email verification</button>
    </form>
  `;
  document.querySelector("#auth-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const email = document.querySelector("#auth-email").value;
    const password = document.querySelector("#auth-password")?.value || "recovery-only";
    const error = document.querySelector("#auth-error");
    try {
      if (view === "recover") {
        setState((draft) => {
          draft.auth.resetRequested = true;
          draft.activity.unshift({ type: "security", text: `Password reset requested for ${email}`, time: nowTime() });
          return draft;
        });
        return;
      }
      if (password.length < 8) throw new Error("Password must be at least 8 characters.");
      const session = mockAuthLogin(email);
      setState((draft) => {
        draft.auth.session = session;
        draft.auth.verified = view === "login";
        draft.activity.unshift({ type: "security", text: `${view === "login" ? "Logged in" : "Signed up"} as ${session.email}`, time: nowTime() });
        return draft;
      });
    } catch (err) {
      error.textContent = err.message;
    }
  });
  document.querySelector("#verify-demo").addEventListener("click", () => {
    setState((draft) => {
      draft.auth.verified = true;
      draft.activity.unshift({ type: "security", text: "Email verification completed", time: nowTime() });
      return draft;
    });
  });
}

function renderOnboarding() {
  const step = state.onboarding.step;
  const steps = [renderUseCaseStep, renderTechnicalStep, renderToolsStep, renderProviderStep];
  app.innerHTML = `
    <main class="onboarding-layout">
      <header class="onboarding-header">
        <div class="logo-lockup">
          <span class="logo-mark" aria-hidden="true">T</span>
          <div><b>TITANOS</b><small>Setup</small></div>
        </div>
        <button class="ghost-action" id="logout-button" type="button">Logout</button>
      </header>
      <section class="onboarding-card">
        <div class="stepper" aria-label="Onboarding progress">
          ${["Workspace", "Technical level", "Tools", "Provider"].map((label, index) => `<span class="${index === step ? "active" : ""}">${index + 1}. ${label}</span>`).join("")}
        </div>
        <div id="onboarding-step"></div>
        <div class="onboarding-actions">
          <button class="ghost-action" id="back-step" type="button" ${step === 0 ? "disabled" : ""}>Back</button>
          <button class="primary-action" id="next-step" type="button">${step === 3 ? "Enter workspace" : "Continue"}</button>
        </div>
      </section>
    </main>
  `;
  steps[step]();
  document.querySelector("#logout-button").addEventListener("click", logout);
  document.querySelector("#back-step").addEventListener("click", () => setState((draft) => {
    draft.onboarding.step = Math.max(0, draft.onboarding.step - 1);
    return draft;
  }));
  document.querySelector("#next-step").addEventListener("click", () => setState((draft) => {
    if (draft.onboarding.step === 3) {
      draft.onboarding.complete = true;
      draft.activity.unshift({ type: "setup", text: "Onboarding completed", time: nowTime() });
    } else {
      draft.onboarding.step += 1;
    }
    return draft;
  }));
}

function renderUseCaseStep() {
  document.querySelector("#onboarding-step").innerHTML = `
    <h2>What are you here to do?</h2>
    <p>Universal is recommended when you want one UI for all purposes.</p>
    <div class="choice-grid">
      ${workspaceModes.map((mode) => `
        <button class="choice-card ${state.preferences.workspaceMode === mode.id ? "selected" : ""}" data-workspace-choice="${mode.id}" type="button">
          <strong>${mode.label}</strong>
          <span>${mode.useCase}</span>
        </button>
      `).join("")}
    </div>
  `;
  document.querySelectorAll("[data-workspace-choice]").forEach((button) => {
    button.addEventListener("click", () => setState((draft) => {
      const mode = workspaceModes.find((item) => item.id === button.dataset.workspaceChoice);
      draft.preferences.workspaceMode = mode.id;
      draft.preferences.visibleTools = [...mode.tools];
      return draft;
    }));
  });
}

function renderTechnicalStep() {
  document.querySelector("#onboarding-step").innerHTML = `
    <h2>How technical should TITANOS feel?</h2>
    <p>Simple hides code-level tools. Developer opens the full power lane.</p>
    <div class="choice-grid four">
      ${Object.entries(technicalLevels).map(([id, level]) => `
        <button class="choice-card ${state.preferences.technicalLevel === id ? "selected" : ""}" data-level-choice="${id}" type="button">
          <strong>${level.label}</strong>
          <span>${level.hiddenTools.length ? `Hides ${level.hiddenTools.slice(0, 3).join(", ")}` : "Shows all operational tools"}</span>
        </button>
      `).join("")}
    </div>
  `;
  document.querySelectorAll("[data-level-choice]").forEach((button) => {
    button.addEventListener("click", () => setState((draft) => {
      draft.preferences.technicalLevel = button.dataset.levelChoice;
      return draft;
    }));
  });
}

function renderToolsStep() {
  const allTools = ["agent", "tasks", "files", "browser", "notes", "automations", "integrations", "calendar", "email", "documents", "spreadsheets", "code", "terminal", "git", "analytics", "approvals"];
  document.querySelector("#onboarding-step").innerHTML = `
    <h2>Choose visible tools</h2>
    <p>You can change this later from Appearance and Layout.</p>
    <div class="tool-grid">
      ${allTools.map((tool) => `
        <label class="tool-toggle">
          <input type="checkbox" data-tool-choice="${tool}" ${state.preferences.visibleTools.includes(tool) ? "checked" : ""} />
          <span>${labelize(tool)}</span>
        </label>
      `).join("")}
    </div>
  `;
  document.querySelectorAll("[data-tool-choice]").forEach((input) => {
    input.addEventListener("change", () => setState((draft) => {
      const tool = input.dataset.toolChoice;
      const set = new Set(draft.preferences.visibleTools);
      input.checked ? set.add(tool) : set.delete(tool);
      draft.preferences.visibleTools = [...set];
      return draft;
    }));
  });
}

function renderProviderStep() {
  document.querySelector("#onboarding-step").innerHTML = `
    <h2>Connect an AI provider</h2>
    <p>Skip is allowed. TITANOS will show a setup checklist until a provider is connected.</p>
    ${renderProviderManager(true)}
  `;
  bindProviderForms();
}

function renderWorkspace() {
  const mode = workspaceModes.find((item) => item.id === state.preferences.workspaceMode) || workspaceModes[0];
  app.innerHTML = `
    <div class="workspace-shell">
      <aside class="sidebar ${state.preferences.sidebarCollapsed ? "collapsed" : ""}">
        <div class="logo-lockup">
          <span class="logo-mark" aria-hidden="true">T</span>
          <div><b>TITANOS</b><small>${mode.label} Workspace</small></div>
        </div>
        <button class="nav-item ${state.preferences.currentRoute === "workspace" ? "active" : ""}" data-route="workspace" type="button">Command Center</button>
        <button class="nav-item ${state.preferences.currentRoute === "providers" ? "active" : ""}" data-route="providers" type="button">API Keys</button>
        <button class="nav-item ${state.preferences.currentRoute === "settings" ? "active" : ""}" data-route="settings" type="button">Settings</button>
        <button class="nav-item ${state.preferences.currentRoute === "permissions" ? "active" : ""}" data-route="permissions" type="button">Permissions</button>
        <button class="nav-item ${state.preferences.currentRoute === "billing" ? "active" : ""}" data-route="billing" type="button">Usage</button>
        <div class="sidebar-footer">
          <button class="icon-button" id="theme-toggle" type="button" aria-label="Toggle theme">◐</button>
          <button class="ghost-action" id="logout-button" type="button">Logout</button>
        </div>
      </aside>
      <main class="workspace-main">
        <header class="workspace-topbar">
          <div>
            <span class="eyebrow">One universal agent. Many specialized workspaces.</span>
            <h1>${mode.label === "Universal" ? "Universal Workspace" : `${mode.label} Workspace`}</h1>
          </div>
          <div class="topbar-actions">
            <label class="select-label">Workspace
              <select id="workspace-switcher">
                ${workspaceModes.map((item) => `<option value="${item.id}" ${item.id === mode.id ? "selected" : ""}>${item.label}</option>`).join("")}
              </select>
            </label>
            <label class="select-label">Mode
              <select id="level-switcher">
                ${Object.entries(technicalLevels).map(([id, item]) => `<option value="${id}" ${id === state.preferences.technicalLevel ? "selected" : ""}>${item.label}</option>`).join("")}
              </select>
            </label>
            <button class="ghost-action" id="open-command-palette" type="button">Command palette</button>
          </div>
        </header>
        <section id="route-panel"></section>
      </main>
    </div>
  `;
  bindWorkspaceShell();
  renderRoute(state.preferences.currentRoute || "workspace");
}

function bindWorkspaceShell() {
  document.querySelector("#logout-button").addEventListener("click", logout);
  document.querySelector("#theme-toggle").addEventListener("click", () => setState((draft) => {
    draft.preferences.theme = draft.preferences.theme === "dark" ? "light" : "dark";
    return draft;
  }));
  document.querySelector("#workspace-switcher").addEventListener("change", (event) => setState((draft) => {
    const mode = workspaceModes.find((item) => item.id === event.target.value);
    draft.preferences.workspaceMode = mode.id;
    if (mode.id !== "custom") draft.preferences.visibleTools = [...mode.tools];
    draft.activity.unshift({ type: "workspace", text: `Switched to ${mode.label} Workspace`, time: nowTime() });
    return draft;
  }));
  document.querySelector("#level-switcher").addEventListener("change", (event) => setState((draft) => {
    draft.preferences.technicalLevel = event.target.value;
    draft.activity.unshift({ type: "settings", text: `Technical level changed to ${technicalLevels[event.target.value].label}`, time: nowTime() });
    return draft;
  }));
  document.querySelectorAll("[data-route]").forEach((button) => {
    button.addEventListener("click", () => {
      setState((draft) => {
        draft.preferences.currentRoute = button.dataset.route;
        return draft;
      });
    });
  });
  document.querySelector("#open-command-palette").addEventListener("click", openCommandPalette);
}

function renderRoute(route) {
  const panel = document.querySelector("#route-panel");
  if (route === "providers") {
    panel.innerHTML = renderSettingsFrame("API Keys and Providers", renderProviderManager(false));
    bindProviderForms();
    return;
  }
  if (route === "settings") {
    panel.innerHTML = renderSettingsFrame("Workspace Settings", renderSettings());
    bindSettings();
    return;
  }
  if (route === "permissions") {
    panel.innerHTML = renderSettingsFrame("Tool Permissions", renderPermissions());
    return;
  }
  if (route === "billing") {
    panel.innerHTML = renderSettingsFrame("Usage and Billing", renderBilling());
    return;
  }
  panel.innerHTML = renderCommandCenter();
  bindCommandCenter();
}

function renderCommandCenter() {
  const mode = workspaceModes.find((item) => item.id === state.preferences.workspaceMode) || workspaceModes[0];
  const missingProvider = Object.values(state.providers).every((item) => !item?.connected);
  return `
    ${missingProvider ? `<div class="setup-banner"><strong>Provider setup needed</strong><span>Add an API key in settings when you are ready. The workspace remains usable with the local runtime.</span></div>` : ""}
    <div class="product-grid">
      <section class="agent-panel">
        <div class="panel-head">
          <div>
            <span class="eyebrow">All-in-one agent</span>
            <h2>Ask anything</h2>
          </div>
          <span class="status-pill">${labelize(state.preferences.technicalLevel)}</span>
        </div>
        <ol class="transcript conversation" id="transcript">
          ${state.agent.conversation.map((item) => `<li><time>${item.time}</time><b>${item.speaker}</b><p>${escapeHtml(item.text)}</p></li>`).join("")}
        </ol>
        <form class="command-line" id="command-form">
          <label for="command-input">Command</label>
          <input id="command-input" autocomplete="off" placeholder="Ask TITANOS to code, research, write, analyze, plan, or automate..." />
          <button type="submit">Run</button>
        </form>
      </section>
      <aside class="context-panel">
        ${renderCurrentRun()}
      </aside>
      <section class="workspace-panels">
        ${renderModePanels(mode)}
      </section>
      <section class="activity-panel logs-panel" aria-label="System Logs">
        <div class="panel-head">
          <div><span class="eyebrow">Activity</span><h2>Timeline</h2></div>
          <button class="ghost-action" id="refresh-backend" type="button">Refresh backend</button>
        </div>
        <div class="timeline">
          ${state.activity.slice(0, 12).map((item) => `<article><span>${item.time}</span><b>${labelize(item.type)}</b><p>${escapeHtml(item.text)}</p></article>`).join("")}
        </div>
      </section>
    </div>
  `;
}

function renderCurrentRun() {
  const run = state.agent.currentRun;
  if (!run) {
    return `
      <div class="panel-head"><div><span class="eyebrow">Plan</span><h2>Ready</h2></div></div>
      <div class="empty-state">
        <strong>No active run</strong>
        <p>Send a request and TITANOS will classify it, choose tools, plan steps, request approvals, and produce a result.</p>
      </div>
      ${renderApprovalQueue()}
    `;
  }
  return `
    <div class="panel-head">
      <div><span class="eyebrow">Detected task</span><h2>${labelize(run.category)}</h2></div>
      <span class="status-pill ${run.status}">${labelize(run.status)}</span>
    </div>
    <div class="tool-strip">${run.selectedTools.map((tool) => `<span>${labelize(tool)}</span>`).join("")}</div>
    <div class="step-list">
      ${run.steps.map((step) => `<article class="${step.status}"><span></span><p>${escapeHtml(step.label)}</p><b>${labelize(step.status)}</b></article>`).join("")}
    </div>
    ${run.sensitive ? `<div class="approval-card"><strong>Approval required</strong><p>This request includes: ${escapeHtml(run.sensitive)}.</p><button class="primary-action" id="approve-current-run" type="button">Approve and continue</button></div>` : ""}
    ${run.result ? `<div class="result-card"><strong>Final result</strong><p>${escapeHtml(run.result)}</p><div>${run.suggestedNextActions.map((item) => `<button class="ghost-action" type="button">${escapeHtml(item)}</button>`).join("")}</div></div>` : ""}
    ${renderApprovalQueue()}
  `;
}

function renderApprovalQueue() {
  if (!state.agent.approvals.length) return "";
  return `
    <div class="approval-list approvals-panel">
      <h3>Approval Queue</h3>
      ${state.agent.approvals.map((item) => `
        <article>
          <b>${escapeHtml(item.action)}</b>
          <p>${escapeHtml(item.prompt)}</p>
          <button class="ghost-action" data-clear-approval="${item.id}" type="button">Mark reviewed</button>
        </article>
      `).join("")}
    </div>
  `;
}

function bindCommandCenter() {
  const form = document.querySelector("#command-form");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.querySelector("#command-input");
    const prompt = input.value.trim();
    if (!prompt) return;
    input.value = "";
    const run = buildAgentRun(prompt, state.preferences.technicalLevel);
    setState((draft) => {
      draft.agent.conversation.push({ speaker: "Operator", text: prompt, time: nowTime() });
      draft.agent.currentRun = run;
      draft.activity.unshift({ type: "agent", text: `Classified request as ${labelize(run.category)}`, time: nowTime() });
      if (run.sensitive) {
        draft.agent.approvals.unshift({ id: run.id, action: run.sensitive, prompt, createdAt: nowTime() });
        draft.agent.conversation.push({ speaker: "TITANOS", text: `I can do this, but ${run.sensitive} needs approval first.`, time: nowTime() });
      }
      return draft;
    });
    if (!run.sensitive) await executeRun(run, prompt);
  });
  const approve = document.querySelector("#approve-current-run");
  if (approve) {
    approve.addEventListener("click", async () => {
      const run = state.agent.currentRun;
      if (!run) return;
      setState((draft) => {
        draft.agent.currentRun.status = "running";
        draft.agent.approvals = draft.agent.approvals.filter((item) => item.id !== run.id);
        draft.activity.unshift({ type: "approval", text: `Approved ${run.sensitive}`, time: nowTime() });
        return draft;
      });
      await executeRun({ ...run, status: "running" }, run.prompt);
    });
  }
  document.querySelectorAll("[data-clear-approval]").forEach((button) => {
    button.addEventListener("click", () => setState((draft) => {
      draft.agent.approvals = draft.agent.approvals.filter((item) => item.id !== button.dataset.clearApproval);
      return draft;
    }));
  });
  document.querySelector("#refresh-backend")?.addEventListener("click", hydrateBackendSignals);
  document.querySelectorAll("[data-custom-tool]").forEach((input) => {
    input.addEventListener("change", () => setState((draft) => {
      const tools = new Set(draft.preferences.visibleTools);
      input.checked ? tools.add(input.dataset.customTool) : tools.delete(input.dataset.customTool);
      draft.preferences.visibleTools = [...tools];
      draft.preferences.customLayout = [...tools];
      draft.activity.unshift({ type: "workspace", text: "Custom workspace layout updated", time: nowTime() });
      return draft;
    }));
  });
}

async function executeRun(run, prompt) {
  let backendMessage = "";
  try {
    const response = await sendMessage(prompt, localStorage.getItem("titanos_session_id"));
    if (response?.session_id) localStorage.setItem("titanos_session_id", response.session_id);
    backendMessage = response?.response || "";
  } catch {
    backendMessage = "";
  }
  await new Promise((resolve) => setTimeout(resolve, 650));
  const complete = completeAgentRun(run);
  if (backendMessage) complete.result = `${complete.result} Backend response: ${backendMessage}`;
  setState((draft) => {
    draft.agent.currentRun = complete;
    draft.agent.history.unshift(complete);
    draft.agent.conversation.push({ speaker: "TITANOS", text: complete.result, time: nowTime() });
    draft.activity.unshift({ type: "result", text: complete.result, time: nowTime() });
    return draft;
  });
}

function renderModePanels(mode) {
  const hidden = technicalLevels[state.preferences.technicalLevel]?.hiddenTools || [];
  const tools = state.preferences.visibleTools.filter((tool) => !hidden.includes(tool));
  const cards = mode.id === "coding"
    ? [
        ["Repo Explorer", "Selected file state, folders, and project context are ready."],
        ["Code Editor", "Editor panel is wired to selected file state for real backend integration."],
        ["Terminal", "Command execution stays behind approvals."],
        ["Git and Diffs", "Status, diffs, tests, and deployment checks live here."],
      ]
    : mode.id === "business"
    ? [["Workflow Dashboard", "Track operations and owners."], ["Reports", "Build summaries from active work."], ["Approvals", "Review sensitive actions."], ["CRM Summary", "Accounts, status, and next steps."]]
    : mode.id === "content"
    ? [["Editor", "Draft content with brand voice checks."], ["Brand Voice", "Tone, rules, and saved examples."], ["Calendar", "Campaign and publishing schedule."], ["Assets", "Library for reusable media and references."]]
    : mode.id === "research"
    ? [["Browser", "Research workspace for source gathering."], ["Sources", "Track credibility and status."], ["Citations", "Notes ready for reports."], ["Document Library", "Keep research artifacts together."]]
    : mode.id === "daily"
    ? [["Calendar", "Meetings and preparation."], ["Inbox", "Email summaries and follow-ups."], ["Reminders", "Personal routines and tasks."], ["Automations", "Repeated daily workflows."]]
    : mode.id === "data"
    ? [["Spreadsheet", "Import and inspect tables."], ["Charts", "Generate analysis views."], ["Insights", "Find anomalies and risks."], ["History", "Track previous analysis runs."]]
    : mode.id === "sales"
    ? [["Leads", "Prioritize contacts."], ["Tickets", "Support conversations."], ["Pipeline", "Deal and status board."], ["Follow-ups", "Draft outbound actions for approval."]]
    : [["Tasks", "Universal action list."], ["Files/Documents", "Workspace artifacts."], ["Browser/Research", "Source gathering."], ["Notes/Knowledge", "Reusable memory and context."], ["Automations", "Reusable workflows."], ["Integrations", "Connected apps and services."]];

  return `
    <div class="panel-head"><div><span class="eyebrow">${mode.label}</span><h2>Workspace tools</h2></div></div>
    <div class="tool-strip">${tools.map((tool) => `<span>${labelize(tool)}</span>`).join("")}</div>
    <div class="card-grid">
      ${cards.map(([title, text]) => `<article class="tool-card"><strong>${title}</strong><p>${text}</p><button class="ghost-action" type="button">Open</button></article>`).join("")}
    </div>
    ${mode.id === "custom" ? renderCustomBuilder() : ""}
  `;
}

function renderCustomBuilder() {
  const all = ["agent", "tasks", "files", "browser", "notes", "automations", "integrations", "calendar", "email", "documents", "spreadsheets", "code", "terminal", "git", "analytics", "approvals"];
  return `
    <div class="custom-builder">
      <h3>Custom Workspace Builder</h3>
      <div class="tool-grid">
        ${all.map((tool) => `
          <label class="tool-toggle">
            <input type="checkbox" data-custom-tool="${tool}" ${state.preferences.visibleTools.includes(tool) ? "checked" : ""} />
            <span>${labelize(tool)}</span>
          </label>
        `).join("")}
      </div>
    </div>
  `;
}

function renderProviderManager(compact) {
  return `
    <div class="provider-grid">
      ${providers.map((provider) => {
        const saved = state.providers[provider.id];
        return `
          <article class="provider-card ${saved?.connected ? "connected" : ""}">
            <div>
              <span class="eyebrow">${saved?.connected ? "Connected" : "Not connected"}</span>
              <h3>${provider.label}</h3>
              <p>${saved?.lastTest ? `Last tested ${new Date(saved.lastTest).toLocaleString()}` : "Add and test this provider without editing project code."}</p>
            </div>
            <form data-provider-form="${provider.id}" class="provider-form">
              ${provider.fields.includes("baseUrl") ? `<label>Base URL<input name="baseUrl" value="${saved?.baseUrl || ""}" placeholder="https://api.example.com or localhost:11434" /></label>` : ""}
              ${provider.fields.includes("apiKey") ? `<label>API key<input name="apiKey" value="" placeholder="${saved?.maskedKey || "Paste key"}" autocomplete="off" /></label>` : ""}
              <label>Model<input name="model" value="${saved?.model || provider.defaultModel}" /></label>
              <p class="provider-secret">Saved key: ${saved?.maskedKey || "Not saved"}</p>
              <p class="form-error" data-provider-error="${provider.id}">${saved?.error || ""}</p>
              <div class="provider-actions">
                <button class="primary-action" type="submit">Save and test</button>
                <button class="ghost-action" data-remove-provider="${provider.id}" type="button">Remove</button>
              </div>
            </form>
          </article>
        `;
      }).join("")}
    </div>
    ${compact ? "" : `<p class="settings-note">Keys are stored through an isolated local secure-storage adapter. Production secret storage can replace this interface without rewriting UI components.</p>`}
  `;
}

function bindProviderForms() {
  document.querySelectorAll("[data-provider-form]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const providerId = form.dataset.providerForm;
      const provider = providers.find((item) => item.id === providerId);
      const data = Object.fromEntries(new FormData(form).entries());
      const previous = state.providers[providerId] || {};
      const apiKey = data.apiKey || previous.secretRef || "";
      const config = { ...data, apiKey };
      const error = document.querySelector(`[data-provider-error="${providerId}"]`);
      error.textContent = "Testing connection...";
      try {
        const result = await testProviderConnection(providerId, config);
        setState((draft) => {
          draft.providers[providerId] = {
            label: provider.label,
            model: data.model,
            baseUrl: data.baseUrl,
            secretRef: apiKey || previous.secretRef,
            maskedKey: data.apiKey ? maskSecret(data.apiKey) : previous.maskedKey,
            connected: true,
            lastTest: result.checkedAt,
            error: "",
          };
          draft.activity.unshift({ type: "provider", text: `${provider.label} connection verified`, time: nowTime() });
          return draft;
        });
      } catch (err) {
        error.textContent = err.message;
        setState((draft) => {
          draft.providers[providerId] = { ...previous, label: provider.label, connected: false, error: err.message };
          return draft;
        });
      }
    });
  });
  document.querySelectorAll("[data-remove-provider]").forEach((button) => {
    button.addEventListener("click", () => setState((draft) => {
      delete draft.providers[button.dataset.removeProvider];
      draft.activity.unshift({ type: "provider", text: "Provider removed", time: nowTime() });
      return draft;
    }));
  });
}

function renderSettingsFrame(title, content) {
  return `<section class="settings-page"><div class="panel-head"><div><span class="eyebrow">Settings</span><h2>${title}</h2></div></div>${content}</section>`;
}

function renderSettings() {
  const all = ["agent", "tasks", "files", "browser", "notes", "automations", "integrations", "calendar", "email", "documents", "spreadsheets", "code", "terminal", "git", "analytics", "approvals"];
  return `
    <div class="settings-grid">
      <article>
        <h3>Account</h3>
        <p>${state.auth.session.email}</p>
        <p>Email ${state.auth.verified ? "verified" : "not verified"}.</p>
      </article>
      <article>
        <h3>Appearance and Layout</h3>
        <label>Theme
          <select id="theme-setting"><option value="dark" ${state.preferences.theme === "dark" ? "selected" : ""}>Dark</option><option value="light" ${state.preferences.theme === "light" ? "selected" : ""}>Light</option></select>
        </label>
      </article>
      <article class="wide">
        <h3>Visible tools</h3>
        <div class="tool-grid">
          ${all.map((tool) => `<label class="tool-toggle"><input type="checkbox" data-settings-tool="${tool}" ${state.preferences.visibleTools.includes(tool) ? "checked" : ""} /><span>${labelize(tool)}</span></label>`).join("")}
        </div>
      </article>
    </div>
  `;
}

function bindSettings() {
  document.querySelector("#theme-setting").addEventListener("change", (event) => setState((draft) => {
    draft.preferences.theme = event.target.value;
    return draft;
  }));
  document.querySelectorAll("[data-settings-tool]").forEach((input) => {
    input.addEventListener("change", () => setState((draft) => {
      const tools = new Set(draft.preferences.visibleTools);
      input.checked ? tools.add(input.dataset.settingsTool) : tools.delete(input.dataset.settingsTool);
      draft.preferences.visibleTools = [...tools];
      return draft;
    }));
  });
}

function renderPermissions() {
  const sensitive = ["Sending email", "Deleting files", "Running terminal commands", "Making purchases", "Publishing content", "Changing provider keys", "Deploying code", "Inviting users", "Exporting private data"];
  return `<div class="settings-grid">${sensitive.map((item) => `<article><h3>${item}</h3><p>Approval required before execution.</p><span class="status-pill">Protected</span></article>`).join("")}</div>`;
}

function renderBilling() {
  return `<div class="settings-grid"><article><h3>Usage</h3><p>Token and provider usage will report here once production billing is attached.</p></article><article><h3>Limits</h3><p>Workspace spending controls and alerts are reserved in the product shell.</p></article></div>`;
}

function openCommandPalette() {
  const options = ["Switch workspace", "Open API keys", "Run first agent task", "Show tool permissions", "Reset local demo"];
  const picked = window.prompt(`Command palette:\n${options.map((item, index) => `${index + 1}. ${item}`).join("\n")}`);
  if (picked === "5") {
    resetProductState();
    state = createInitialState();
    render();
  }
}

async function hydrateBackendSignals() {
  try {
    const [health, body, doctor, memory, runs, approvals] = await Promise.allSettled([
      fetchProviderHealth(),
      fetchBodyHealth(),
      fetchDoctor(),
      fetchMemory(),
      fetchRuns(),
      fetchApprovals(),
    ]);
    const entries = [];
    if (health.status === "fulfilled") entries.push(`Provider health loaded: ${(health.value.providers || []).length} provider(s)`);
    if (body.status === "fulfilled") entries.push(`Body health loaded: ${(body.value.systems || []).length} system(s)`);
    if (doctor.status === "fulfilled") entries.push(`Diagnostics ready: ${doctor.value.os || "unknown OS"}`);
    if (memory.status === "fulfilled") entries.push(`Memory records available: ${(memory.value.memories || []).length}`);
    if (runs.status === "fulfilled") entries.push(`Run history available: ${(runs.value.runs || []).length}`);
    if (approvals.status === "fulfilled") entries.push(`Backend approvals available: ${(approvals.value.approvals || []).length}`);
    if (entries.length) {
      setState((draft) => {
        entries.forEach((text) => draft.activity.unshift({ type: "backend", text, time: nowTime() }));
        return draft;
      });
    }
  } catch {
    // The product UI remains usable through local adapters when backend services are offline.
  }
}

function logout() {
  localStorage.removeItem("titanos_token");
  setState((draft) => {
    draft.auth.session = null;
    return draft;
  });
}

function labelize(value) {
  return String(value).replace(/[_-]/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text ?? "";
  return div.innerHTML;
}
