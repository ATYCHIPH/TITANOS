const fs = require("node:fs");
const net = require("node:net");
const path = require("node:path");

const DEFAULT_DESKTOP_PORT = 18789;
const LOOPBACK_HOST = "127.0.0.1";

function normalizePort(value, fallback = DEFAULT_DESKTOP_PORT) {
  const port = Number(value || fallback);
  if (!Number.isInteger(port) || port < 1024 || port > 65535) {
    return fallback;
  }
  return port;
}

function backendUrl(port) {
  return `http://${LOOPBACK_HOST}:${normalizePort(port)}`;
}

function canConnect(port, timeoutMs = 650) {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host: LOOPBACK_HOST, port: normalizePort(port) });
    socket.setTimeout(timeoutMs);
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

async function findBackendPort(preferredPort, options = {}) {
  const start = normalizePort(preferredPort);
  const attempts = Math.max(1, Number(options.attempts || 20));
  const canConnectFn = options.canConnect || canConnect;

  for (let offset = 0; offset < attempts; offset += 1) {
    const port = start + offset;
    if (port > 65535) break;
    if (!(await canConnectFn(port))) return port;
  }
  throw new Error(`No available TITANOS desktop backend port starting at ${start}.`);
}

function desktopPaths(userDataPath) {
  const runtimeDir = path.join(userDataPath, "runtime");
  const logDir = path.join(userDataPath, "logs");
  return {
    runtimeDir,
    logDir,
    desktopLog: path.join(logDir, "desktop.log"),
    backendOutLog: path.join(logDir, "backend.out.log"),
    backendErrLog: path.join(logDir, "backend.err.log"),
    jwtSecret: path.join(runtimeDir, "desktop.jwt.secret"),
  };
}

function ensureDesktopPaths(userDataPath) {
  const paths = desktopPaths(userDataPath);
  fs.mkdirSync(paths.runtimeDir, { recursive: true });
  fs.mkdirSync(paths.logDir, { recursive: true });
  return paths;
}

function resolveBackendCommand({ appIsPackaged, resourcesPath, rootDir, port, platform = process.platform, python } = {}) {
  const backendPort = normalizePort(port);
  const exeName = platform === "win32" ? "titanos-backend.exe" : "titanos-backend";
  const packagedBackend = path.join(resourcesPath || "", "backend", exeName);

  if (appIsPackaged) {
    if (!fs.existsSync(packagedBackend)) {
      throw new Error(`Bundled backend not found at ${packagedBackend}.`);
    }
    return {
      command: packagedBackend,
      args: ["app", "--port", String(backendPort)],
      cwd: path.dirname(packagedBackend),
      packaged: true,
    };
  }

  return {
    command: python || process.env.TITANOS_PYTHON || "python",
    args: ["-m", "titanos", "app", "--port", String(backendPort)],
    cwd: rootDir,
    packaged: false,
  };
}

function resolveUiEntry(rootDir) {
  const canonical = path.join(rootDir, "desktop-ui", "index.html");
  const fallback = path.join(rootDir, "ui", "index.html");
  if (fs.existsSync(canonical)) {
    return { entry: canonical, source: "react" };
  }
  return { entry: fallback, source: "legacy" };
}

async function waitForBackend(port, timeoutMs, options = {}) {
  const deadline = Date.now() + timeoutMs;
  const canConnectFn = options.canConnect || canConnect;
  while (Date.now() < deadline) {
    if (await canConnectFn(port)) return true;
    await new Promise((resolve) => setTimeout(resolve, options.intervalMs || 300));
  }
  return false;
}

module.exports = {
  DEFAULT_DESKTOP_PORT,
  LOOPBACK_HOST,
  backendUrl,
  canConnect,
  desktopPaths,
  ensureDesktopPaths,
  findBackendPort,
  normalizePort,
  resolveBackendCommand,
  resolveUiEntry,
  waitForBackend,
};
