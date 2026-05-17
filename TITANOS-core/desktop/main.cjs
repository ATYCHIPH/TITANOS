const { app, BrowserWindow, dialog, ipcMain, shell } = require("electron");
const { spawn } = require("node:child_process");
const crypto = require("node:crypto");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const {
  DEFAULT_DESKTOP_PORT,
  backendUrl,
  canConnect,
  ensureDesktopPaths,
  findBackendPort,
  resolveBackendCommand,
  resolveUiEntry,
  waitForBackend,
} = require("./runtime.cjs");

const ROOT_DIR = path.resolve(__dirname, "..");
const PREFERRED_BACKEND_PORT = Number(process.env.TITANOS_DESKTOP_PORT || DEFAULT_DESKTOP_PORT);
const WINDOW_ICON = path.join(ROOT_DIR, "assets", "icon.ico");
let uiEntry = resolveUiEntry(ROOT_DIR);

let mainWindow;
let backendProcess;
let ownsBackend = false;
let backendPort = PREFERRED_BACKEND_PORT;
let backendStatus = {
  state: "starting",
  owned: false,
  message: "Backend has not started yet.",
  startedAt: null,
  exitedAt: null,
  exitCode: null,
};

const singleInstanceLock = app.requestSingleInstanceLock();
if (!singleInstanceLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

// Uncaught exception handlers
process.on("uncaughtException", (error) => {
  writeDesktopLog(`[CRITICAL] Uncaught exception in main process: ${error.stack}`);
});

process.on("unhandledRejection", (reason) => {
  writeDesktopLog(`[CRITICAL] Unhandled promise rejection: ${reason}`);
});

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1040,
    minHeight: 720,
    title: "TITANOS",
    icon: WINDOW_ICON,
    backgroundColor: "#080b0f",
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      additionalArguments: [`--titanos-api-base=${backendUrl(backendPort)}`],
    },
  });

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.webContents.on("console-message", (_event, level, message, line, sourceId) => {
    writeDesktopLog(`[renderer:${level}] ${message} (${sourceId}:${line})`);
  });

  mainWindow.webContents.on("did-fail-load", (_event, errorCode, errorDescription, validatedURL) => {
    writeDesktopLog(`[renderer-load-failed] ${errorCode} ${errorDescription} ${validatedURL}`);
  });

  // Renderer Crash Recovery Hook
  mainWindow.webContents.on("render-process-gone", (event, details) => {
    writeDesktopLog(`[CRITICAL] Render process gone. Reason: ${details.reason}, Exit Code: ${details.exitCode}`);
    dialog.showMessageBox({
      type: "error",
      title: "TITANOS UI Crashed",
      message: "The operator interface has encountered a fatal crash.",
      detail: `Reason: ${details.reason} (Code: ${details.exitCode}). Press OK to reload the workspace.`,
      buttons: ["Reload App", "Exit"]
    }).then(({ response }) => {
      if (response === 0) {
        app.relaunch();
        app.exit(0);
      } else {
        app.quit();
      }
    });
  });

  // Renderer Unresponsive Recovery Hook
  mainWindow.webContents.on("unresponsive", () => {
    writeDesktopLog(`[WARNING] Render process unresponsive.`);
    dialog.showMessageBox({
      type: "warning",
      title: "TITANOS Unresponsive",
      message: "The operator interface is not responding.",
      buttons: ["Wait", "Reload App"]
    }).then(({ response }) => {
      if (response === 1) {
        app.relaunch();
        app.exit(0);
      }
    });
  });

  uiEntry = resolveUiEntry(ROOT_DIR);
  writeDesktopLog(`loading ${uiEntry.source} UI from ${uiEntry.entry}`);
  await mainWindow.loadFile(uiEntry.entry);
}

async function startBackendIfNeeded() {
  if (process.env.TITANOS_DESKTOP_NO_BACKEND === "1") {
    backendStatus = {
      ...backendStatus,
      state: "disabled",
      message: "Desktop backend launch is disabled for this run.",
    };
    return backendStatus;
  }

  if (await canReachRuntime(PREFERRED_BACKEND_PORT)) {
    backendPort = PREFERRED_BACKEND_PORT;
    backendStatus = {
      state: "external",
      owned: false,
      message: `Connected to an existing backend on internal port ${backendPort}.`,
      startedAt: new Date().toISOString(),
      exitedAt: null,
      exitCode: null,
    };
    return backendStatus;
  }

  backendPort = await findBackendPort(PREFERRED_BACKEND_PORT);
  if (backendPort !== PREFERRED_BACKEND_PORT) {
    writeDesktopLog(`preferred port ${PREFERRED_BACKEND_PORT} busy; using ${backendPort}`);
  }

  let backend;
  try {
    backend = resolveBackendCommand({
      appIsPackaged: app.isPackaged,
      resourcesPath: process.resourcesPath,
      rootDir: ROOT_DIR,
      port: backendPort,
    });
  } catch (error) {
    backendStatus = {
      ...backendStatus,
      state: "missing",
      message: error.message,
    };
    dialog.showMessageBox({
      type: "error",
      title: "TITANOS backend missing",
      message: "The bundled TITANOS backend could not be found.",
      detail: error.message,
    });
    return backendStatus;
  }

  const paths = ensureDesktopPaths(app.getPath("userData"));
  const out = fs.openSync(paths.backendOutLog, "a");
  const err = fs.openSync(paths.backendErrLog, "a");
  writeDesktopLog(`launching ${backend.command} ${backend.args.join(" ")}`);
  backendProcess = spawn(backend.command, backend.args, {
    cwd: backend.cwd,
    env: {
      ...process.env,
      TITANOS_DESKTOP_MODE: "1",
      TITANOS_HOST: "127.0.0.1",
      TITANOS_PORT: String(backendPort),
      TITANOS_DATA_DIR: paths.runtimeDir,
      TITANOS_ENVIRONMENT: app.isPackaged ? "production" : "development",
      TITANOS_JWT_SECRET: getDesktopSecret(),
      PYDANTIC_DISABLE_PLUGINS: "__all__",
    },
    windowsHide: true,
    stdio: ["ignore", out, err],
  });
  ownsBackend = true;
  backendProcess.unref();

  backendStatus = {
    state: "starting",
    owned: true,
    message: `Launching backend on internal port ${backendPort}.`,
    startedAt: new Date().toISOString(),
    exitedAt: null,
    exitCode: null,
  };

  backendProcess.once("exit", (code, signal) => {
    backendStatus = {
      ...backendStatus,
      state: "crashed",
      owned: false,
      message: `Backend exited${signal ? ` by ${signal}` : ""}.`,
      exitedAt: new Date().toISOString(),
      exitCode: code,
    };
    writeDesktopLog(`backend exited code=${code ?? "null"} signal=${signal ?? "null"}`);
    backendProcess = null;
    ownsBackend = false;
    mainWindow?.webContents.send("titanos:backend-status", getRuntimeInfo());
  });

  const started = await waitForRuntime(backendPort, 90000);
  if (!started) {
    backendStatus = {
      ...backendStatus,
      state: "timeout",
      message: "The backend did not become ready before the startup timeout.",
    };
    dialog.showMessageBox({
      type: "warning",
      title: "TITANOS backend fallback",
      message: "TITANOS opened with the desktop UI runtime. The Python backend did not start in time.",
      detail: "The app still runs, but backend-backed tools will use desktop fallback data until the runtime is available.",
    });
    return backendStatus;
  }

  backendStatus = {
    ...backendStatus,
    state: "ready",
    message: `Backend ready on internal port ${backendPort}.`,
  };
  return backendStatus;
}

function requestBackend(pathname, options = {}) {
  return new Promise((resolve, reject) => {
    const method = options.method || "GET";
    const body = options.body ? Buffer.from(options.body) : null;
    const request = http.request(
      {
        hostname: "127.0.0.1",
        port: normalizeBackendPort(options.port || backendPort),
        path: pathname,
        method,
        timeout: options.timeoutMs || 30000,
        headers: {
          "content-type": "application/json",
          ...(body ? { "content-length": body.length } : {}),
          ...(options.headers || {}),
        },
      },
      (response) => {
        let text = "";
        response.setEncoding("utf8");
        response.on("data", (chunk) => {
          text += chunk;
        });
        response.on("end", () => {
          let data = null;
          if (text) {
            try {
              data = JSON.parse(text);
            } catch {
              data = text;
            }
          }
          resolve({
            ok: response.statusCode >= 200 && response.statusCode < 300,
            status: response.statusCode,
            statusText: response.statusMessage,
            data,
            text,
          });
        });
      },
    );
    request.on("timeout", () => request.destroy(new Error(`${method} ${pathname} timed out`)));
    request.on("error", reject);
    if (body) request.write(body);
    request.end();
  });
}

function normalizeBackendPort(port) {
  const value = Number(port || backendPort || PREFERRED_BACKEND_PORT);
  return Number.isInteger(value) ? value : PREFERRED_BACKEND_PORT;
}

async function canReachRuntime(port) {
  try {
    const response = await requestBackend("/runtime", { port, timeoutMs: 1000 });
    return response.ok && response.data && response.data.mode === "desktop";
  } catch {
    return false;
  }
}

async function waitForRuntime(port, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await canReachRuntime(port)) return true;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  return false;
}

function getDesktopSecret() {
  const paths = ensureDesktopPaths(app.getPath("userData"));
  if (fs.existsSync(paths.jwtSecret)) {
    return fs.readFileSync(paths.jwtSecret, "utf8").trim();
  }
  const secret = crypto.randomBytes(48).toString("hex");
  fs.writeFileSync(paths.jwtSecret, secret, { mode: 0o600 });
  return secret;
}

function writeDesktopLog(message) {
  try {
    const paths = ensureDesktopPaths(app.getPath("userData"));
    fs.appendFileSync(paths.desktopLog, `${new Date().toISOString()} ${message}\n`);
  } catch {
    // Logging must never block app startup.
  }
}

function getRuntimeInfo() {
  const paths = ensureDesktopPaths(app.getPath("userData"));
  return {
    apiBase: backendUrl(backendPort),
    backend: backendStatus,
    backendPort,
    dataDir: paths.runtimeDir,
    logDir: paths.logDir,
    logs: {
      desktop: paths.desktopLog,
      backendOut: paths.backendOutLog,
      backendErr: paths.backendErrLog,
    },
    ui: uiEntry,
    packaged: app.isPackaged,
    platform: process.platform,
    version: app.getVersion(),
  };
}

async function restartBackend() {
  if (backendProcess && ownsBackend) {
    backendProcess.kill();
    backendProcess = null;
    ownsBackend = false;
  }
  backendStatus = {
    ...backendStatus,
    state: "restarting",
    message: "Restarting backend.",
    exitedAt: null,
    exitCode: null,
  };
  await startBackendIfNeeded();
  mainWindow?.webContents.send("titanos:backend-status", getRuntimeInfo());
  return getRuntimeInfo();
}

ipcMain.handle("titanos:get-runtime-info", () => getRuntimeInfo());
ipcMain.handle("titanos:restart-backend", () => restartBackend());
ipcMain.handle("titanos:api-fetch", async (_event, endpoint, options = {}) => {
  if (!endpoint || typeof endpoint !== "string" || !endpoint.startsWith("/")) {
    return { ok: false, status: 400, statusText: "Bad Request", data: { detail: "Invalid API endpoint" } };
  }
  try {
    const response = await requestBackend(endpoint, options);
    if (response.ok && backendStatus.state !== "ready" && backendStatus.state !== "external") {
      backendStatus = {
        ...backendStatus,
        state: "ready",
        message: `Backend ready on internal port ${backendPort}.`,
        exitCode: null,
        exitedAt: null,
      };
      mainWindow?.webContents.send("titanos:backend-status", getRuntimeInfo());
    }
    return response;
  } catch (error) {
    writeDesktopLog(`[api-fetch-failed] ${endpoint}: ${error.message}`);
    return { ok: false, status: 503, statusText: "Backend Unavailable", data: { detail: error.message } };
  }
});

ipcMain.handle("titanos:read-log-file", async (event, logType) => {
  try {
    const paths = ensureDesktopPaths(app.getPath("userData"));
    let filePath;
    if (logType === 'desktop') filePath = paths.desktopLog;
    else if (logType === 'backendOut') filePath = paths.backendOutLog;
    else if (logType === 'backendErr') filePath = paths.backendErrLog;
    else return `[Error] Unknown log type: ${logType}`;

    if (!fs.existsSync(filePath)) {
      return `[System] Log file does not exist yet at: ${filePath}`;
    }
    const stat = fs.statSync(filePath);
    // Limit reading size to last 500KB to avoid IPC bottleneck
    const maxSize = 500 * 1024;
    const streamSize = Math.min(stat.size, maxSize);
    const fd = fs.openSync(filePath, "r");
    const buffer = Buffer.alloc(streamSize);
    fs.readSync(fd, buffer, 0, streamSize, stat.size - streamSize);
    fs.closeSync(fd);
    return buffer.toString("utf8");
  } catch (error) {
    return `[Error] Failed to read log file: ${error.message}`;
  }
});

ipcMain.handle("titanos:export-logs-dialog", async () => {
  try {
    const paths = ensureDesktopPaths(app.getPath("userData"));
    const { filePath } = await dialog.showSaveDialog(mainWindow, {
      title: "Export TITANOS Logs",
      defaultPath: path.join(app.getPath("downloads"), `titanos-logs-${Date.now()}.txt`),
      filters: [{ name: "Text Files", extensions: ["txt", "log"] }]
    });
    if (!filePath) return { success: false, cancelled: true };

    let combinedLogs = "";
    if (fs.existsSync(paths.desktopLog)) {
      combinedLogs += `=== DESKTOP LOG ===\n${fs.readFileSync(paths.desktopLog, "utf8")}\n\n`;
    }
    if (fs.existsSync(paths.backendOutLog)) {
      combinedLogs += `=== BACKEND OUT LOG ===\n${fs.readFileSync(paths.backendOutLog, "utf8")}\n\n`;
    }
    if (fs.existsSync(paths.backendErrLog)) {
      combinedLogs += `=== BACKEND ERR LOG ===\n${fs.readFileSync(paths.backendErrLog, "utf8")}\n\n`;
    }

    fs.writeFileSync(filePath, combinedLogs, "utf8");
    return { success: true, path: filePath };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

app.whenReady().then(async () => {
  app.setName("TITANOS");
  await startBackendIfNeeded();
  await createWindow();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

app.on("before-quit", () => {
  if (backendProcess && ownsBackend) {
    backendProcess.kill();
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
