const { app, BrowserWindow, dialog, ipcMain, shell } = require("electron");
const { spawn } = require("node:child_process");
const crypto = require("node:crypto");
const net = require("node:net");
const fs = require("node:fs");
const path = require("node:path");

const ROOT_DIR = path.resolve(__dirname, "..");
const UI_ENTRY = path.join(ROOT_DIR, "ui", "index.html");
const BACKEND_PORT = Number(process.env.TITANOS_DESKTOP_PORT || 18789);
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;

let mainWindow;
let backendProcess;
let ownsBackend = false;

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1040,
    minHeight: 720,
    title: "TITANOS",
    backgroundColor: "#080b0f",
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      additionalArguments: [`--titanos-api-base=${BACKEND_URL}`],
    },
  });

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  await mainWindow.loadFile(UI_ENTRY);
}

async function startBackendIfNeeded() {
  if (process.env.TITANOS_DESKTOP_NO_BACKEND === "1") return;
  if (await canConnect(BACKEND_PORT)) return;

  const backend = resolveBackendCommand();
  const logDir = path.join(app.getPath("userData"), "logs");
  fs.mkdirSync(logDir, { recursive: true });
  const out = fs.openSync(path.join(logDir, "backend.out.log"), "a");
  const err = fs.openSync(path.join(logDir, "backend.err.log"), "a");
  fs.appendFileSync(path.join(logDir, "desktop.log"), `${new Date().toISOString()} launching ${backend.command} ${backend.args.join(" ")}\n`);
  backendProcess = spawn(backend.command, backend.args, {
    cwd: backend.cwd,
    env: {
      ...process.env,
      TITANOS_DESKTOP_MODE: "1",
      TITANOS_HOST: "127.0.0.1",
      TITANOS_PORT: String(BACKEND_PORT),
      TITANOS_DATA_DIR: path.join(app.getPath("userData"), "runtime"),
      TITANOS_ENVIRONMENT: app.isPackaged ? "production" : "development",
      TITANOS_JWT_SECRET: getDesktopSecret(),
      PYDANTIC_DISABLE_PLUGINS: "__all__",
    },
    windowsHide: true,
    stdio: ["ignore", out, err],
  });
  ownsBackend = true;
  backendProcess.unref();

  const started = await waitForBackend(BACKEND_PORT, 8000);
  if (!started) {
    dialog.showMessageBox({
      type: "warning",
      title: "TITANOS backend fallback",
      message: "TITANOS opened with the local UI runtime. The Python backend did not start in time.",
      detail: "The app still runs, but backend-backed tools will use desktop fallback data until the runtime is available.",
    });
  }
}

function getDesktopSecret() {
  const secretDir = path.join(app.getPath("userData"), "runtime");
  const secretPath = path.join(secretDir, "desktop.jwt.secret");
  fs.mkdirSync(secretDir, { recursive: true });
  if (fs.existsSync(secretPath)) {
    return fs.readFileSync(secretPath, "utf8").trim();
  }
  const secret = crypto.randomBytes(48).toString("hex");
  fs.writeFileSync(secretPath, secret, { mode: 0o600 });
  return secret;
}

function resolveBackendCommand() {
  const exeName = process.platform === "win32" ? "titanos-backend.exe" : "titanos-backend";
  const packagedBackend = path.join(process.resourcesPath || "", "backend", exeName);
  if (app.isPackaged) {
    return {
      command: packagedBackend,
      args: ["app", "--port", String(BACKEND_PORT)],
      cwd: path.dirname(packagedBackend),
    };
  }

  const python = process.env.TITANOS_PYTHON || "python";
  return {
    command: python,
    args: ["-m", "titanos", "app", "--port", String(BACKEND_PORT)],
    cwd: ROOT_DIR,
  };
}

function canConnect(port) {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host: "127.0.0.1", port });
    socket.setTimeout(650);
    socket.once("connect", () => {
      socket.destroy();
      resolve(true);
    });
    socket.once("timeout", () => {
      socket.destroy();
      resolve(false);
    });
    socket.once("error", () => resolve(false));
  });
}

async function waitForBackend(port, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await canConnect(port)) return true;
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  return false;
}

ipcMain.handle("titanos:get-runtime-info", () => ({
  apiBase: BACKEND_URL,
  packaged: app.isPackaged,
  platform: process.platform,
  version: app.getVersion(),
}));

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
