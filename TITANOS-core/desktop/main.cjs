const { app, BrowserWindow, dialog, ipcMain, shell } = require("electron");
const { spawn } = require("node:child_process");
const net = require("node:net");
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

  const python = process.env.TITANOS_PYTHON || "python";
  backendProcess = spawn(
    python,
    ["-m", "titanos", "app", "--port", String(BACKEND_PORT)],
    {
      cwd: ROOT_DIR,
      env: {
        ...process.env,
        TITANOS_HOST: "127.0.0.1",
        TITANOS_PORT: String(BACKEND_PORT),
      },
      windowsHide: true,
      stdio: "ignore",
    },
  );
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
