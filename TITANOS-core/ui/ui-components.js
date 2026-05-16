// ui-components.js

const states = ["idle", "thinking", "speaking"];
const affects = ["curious", "focused", "quiet", "absorbing", "watchful"];

export class UIComponents {
  constructor() {
    this.elements = {
      clock: document.querySelector("#clock"),
      pulseState: document.querySelector("#pulse-state"),
      runtimeState: document.querySelector("#runtime-state"),
      coherence: document.querySelector("#coherence"),
      drift: document.querySelector("#drift"),
      affect: document.querySelector("#affect"),
      transcript: document.querySelector("#transcript"),
      commandForm: document.querySelector("#command-form"),
      commandInput: document.querySelector("#command-input"),
      clearTranscript: document.querySelector("#clear-transcript"),
      stateButtons: [...document.querySelectorAll(".state-pill")],
      tabs: [...document.querySelectorAll(".tab")],
      bodyRows: [...document.querySelectorAll(".body-row")],
      activeCount: document.querySelector("#active-count"),
      throughput: document.querySelector("#throughput"),
      throughputSlider: document.querySelector("#throughput-slider"),
      quietToggle: document.querySelector("#quiet-toggle"),
      quietLine: document.querySelector("#quiet-line"),
      simulateBuild: document.querySelector("#simulate-build"),
      buildStack: document.querySelector("#build-stack"),
      providerCards: [...document.querySelectorAll(".provider-card")],
      activeProvider: document.querySelector("#active-provider"),
      canvas: document.querySelector("#mesh-canvas"),
      stateCycle: document.querySelector("#state-cycle"),
      themeToggle: document.querySelector("#theme-toggle"),
      logViewer: document.querySelector("#log-viewer"),
      clearLogs: document.querySelector("#clear-logs"),
      panels: {
        mesh: document.querySelector(".pulse-panel"),
        memory: document.querySelector(".memory-panel"),
        history: document.querySelector(".history-panel"),
        approvals: document.querySelector(".approvals-panel"),
        forge: document.querySelector(".forge-panel"),
        logs: document.querySelector(".logs-panel")
      }
    };

    this.ctx = this.elements.canvas.getContext("2d");
    this.stateIndex = 0;
    this.frame = 0;
    this.nodes = Array.from({ length: 42 }, (_, index) => ({
      x: (index * 73) % 560,
      y: (index * 113) % 360,
      vx: ((index % 5) - 2) * 0.18,
      vy: ((index % 7) - 3) * 0.12,
    }));

    this.init();
  }

  init() {
    this.updateClock();
    this.resizeCanvas();
    this.setState("idle");
    this.drawMesh = this.drawMesh.bind(this);
    requestAnimationFrame(this.drawMesh);
    this.loadTheme();
  }

  updateClock() {
    this.elements.clock.textContent = new Date().toLocaleTimeString([], { hour12: false });
  }

  setState(nextState) {
    this.stateIndex = states.indexOf(nextState);
    if (this.stateIndex < 0) this.stateIndex = 0;

    this.elements.stateButtons.forEach((button) => {
      button.classList.toggle("active", button.dataset.state === states[this.stateIndex]);
    });

    this.elements.pulseState.textContent = states[this.stateIndex];
    this.elements.runtimeState.textContent = states[this.stateIndex] === "idle" ? "Standby" : "Active";
    this.elements.affect.textContent = affects[(this.stateIndex + Math.floor(this.frame / 180)) % affects.length];
  }

  appendMessage(speaker, text) {
    const item = document.createElement("li");
    const now = new Date().toLocaleTimeString([], { hour12: false });
    item.innerHTML = `<time>${now}</time><b>${speaker}</b><p></p>`;
    item.querySelector("p").textContent = text;
    this.elements.transcript.append(item);
    this.elements.transcript.scrollTop = this.elements.transcript.scrollHeight;
  }

  appendLog(level, text) {
    const item = document.createElement("div");
    item.className = `log-entry ${level}`;
    const now = new Date().toLocaleTimeString([], { hour12: false });
    item.innerHTML = `<span class="log-time">[${now}]</span><span class="log-level">${level.toUpperCase()}</span><span class="log-msg">${text}</span>`;
    this.elements.logViewer.append(item);
    this.elements.logViewer.scrollTop = this.elements.logViewer.scrollHeight;
  }

  resizeCanvas() {
    const bounds = this.elements.canvas.getBoundingClientRect();
    const scale = window.devicePixelRatio || 1;
    this.elements.canvas.width = Math.max(320, Math.floor(bounds.width * scale));
    this.elements.canvas.height = Math.max(320, Math.floor(bounds.height * scale));
    this.ctx.setTransform(scale, 0, 0, scale, 0, 0);
  }

  drawMesh() {
    const width = this.elements.canvas.clientWidth;
    const height = this.elements.canvas.clientHeight;
    this.frame += 1;
    this.ctx.clearRect(0, 0, width, height);

    this.nodes.forEach((node) => {
      node.x += node.vx;
      node.y += node.vy;
      if (node.x < 0 || node.x > width) node.vx *= -1;
      if (node.y < 0 || node.y > height) node.vy *= -1;
    });

    this.ctx.lineWidth = 1;
    for (let i = 0; i < this.nodes.length; i += 1) {
      for (let j = i + 1; j < this.nodes.length; j += 1) {
        const a = this.nodes[i];
        const b = this.nodes[j];
        const distance = Math.hypot(a.x - b.x, a.y - b.y);
        if (distance < 118) {
          this.ctx.strokeStyle = `rgba(118, 217, 238, ${0.18 - distance / 780})`;
          this.ctx.beginPath();
          this.ctx.moveTo(a.x, a.y);
          this.ctx.lineTo(b.x, b.y);
          this.ctx.stroke();
        }
      }
    }

    this.nodes.forEach((node, index) => {
      this.ctx.fillStyle = index % 3 === 0 ? "#88f0b1" : "#76d9ee";
      this.ctx.globalAlpha = 0.68;
      this.ctx.beginPath();
      this.ctx.arc(node.x, node.y, index % 5 === 0 ? 2.6 : 1.8, 0, Math.PI * 2);
      this.ctx.fill();
      this.ctx.globalAlpha = 1;
    });

    const coherenceValue = 0.982 + Math.sin(this.frame / 84) * 0.009;
    const driftValue = 0.014 + Math.sin(this.frame / 65) * 0.012;
    this.elements.coherence.textContent = coherenceValue.toFixed(4);
    this.elements.drift.textContent = `${driftValue >= 0 ? "+" : ""}${driftValue.toFixed(3)}`;

    requestAnimationFrame(this.drawMesh);
  }

  updateBodyStatus(status) {
    this.elements.bodyRows.forEach(row => {
      const sys = row.dataset.system.toLowerCase();
      if (status[sys] === "ready" || status[sys] === "active") {
        row.classList.add("online");
        row.classList.remove("offline");
      }
    });
    const online = this.elements.bodyRows.filter((item) => item.classList.contains("online")).length;
    this.elements.activeCount.textContent = String(online);
  }

  updateProviderStatus(providers) {
    providers.forEach(p => {
      const card = this.elements.providerCards.find(c => c.dataset.provider.toLowerCase() === p.name.toLowerCase());
      if (card) {
        card.classList.toggle("offline", p.status === "offline");
        card.classList.toggle("online", p.status === "online");
      }
    });
  }

  toggleTheme() {
    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    const newTheme = isLight ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("titanos_theme", newTheme);
  }

  loadTheme() {
    const savedTheme = localStorage.getItem("titanos_theme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);
  }
}
