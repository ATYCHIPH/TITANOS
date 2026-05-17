const { spawn } = require("node:child_process");
const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "..");
const exeName = process.platform === "win32" ? "titanos-backend.exe" : "titanos-backend";
const backendExe = path.join(root, "desktop-runtime", "backend", exeName);
const manifestPath = path.join(root, "desktop-runtime", "backend", "backend-manifest.json");
const port = Number(process.env.TITANOS_BACKEND_SMOKE_PORT || 18879);
const timeoutMs = Number(process.env.TITANOS_BACKEND_SMOKE_TIMEOUT_MS || 90000);

function fail(message) {
  console.error(message);
  process.exit(1);
}

function requestJson(pathname) {
  return new Promise((resolve, reject) => {
    const request = http.get(
      {
        hostname: "127.0.0.1",
        port,
        path: pathname,
        timeout: 1000,
      },
      (response) => {
        let body = "";
        response.setEncoding("utf8");
        response.on("data", (chunk) => {
          body += chunk;
        });
        response.on("end", () => {
          if (response.statusCode < 200 || response.statusCode >= 300) {
            reject(new Error(`${pathname} returned HTTP ${response.statusCode}: ${body}`));
            return;
          }
          try {
            resolve(JSON.parse(body));
          } catch (error) {
            reject(new Error(`${pathname} returned invalid JSON: ${error.message}`));
          }
        });
      },
    );
    request.on("timeout", () => {
      request.destroy(new Error(`${pathname} timed out`));
    });
    request.on("error", reject);
  });
}

async function waitForReady() {
  const deadline = Date.now() + timeoutMs;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const ready = await requestJson("/readyz");
      if (ready.status === "ready") return;
      lastError = new Error(`/readyz returned ${JSON.stringify(ready)}`);
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 400));
  }
  throw lastError || new Error("Backend did not become ready");
}

async function main() {
  if (!fs.existsSync(backendExe)) {
    fail(`Staged backend executable not found at ${backendExe}. Run npm run desktop:stage-backend first.`);
  }
  if (!fs.existsSync(manifestPath)) {
    fail(`Backend manifest not found at ${manifestPath}. Run npm run desktop:stage-backend first.`);
  }

  const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), "titanos-backend-smoke-"));
  const child = spawn(backendExe, ["app", "--port", String(port)], {
    cwd: path.dirname(backendExe),
    env: {
      ...process.env,
      TITANOS_DESKTOP_MODE: "1",
      TITANOS_HOST: "127.0.0.1",
      TITANOS_PORT: String(port),
      TITANOS_DATA_DIR: dataDir,
      TITANOS_ENVIRONMENT: "production",
      TITANOS_JWT_SECRET: "backend-smoke-test-secret",
      PYDANTIC_DISABLE_PLUGINS: "__all__",
    },
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });

  let output = "";
  child.stdout.on("data", (chunk) => {
    output += chunk.toString();
  });
  child.stderr.on("data", (chunk) => {
    output += chunk.toString();
  });

  try {
    await waitForReady();
    const runtime = await requestJson("/runtime");
    if (runtime.mode !== "desktop") {
      throw new Error(`/runtime expected desktop mode, got ${JSON.stringify(runtime)}`);
    }
    console.log(`Backend smoke passed on 127.0.0.1:${port}`);
  } catch (error) {
    console.error(output.trim());
    fail(`Backend smoke failed: ${error.message}`);
  } finally {
    await stopProcessTree(child);
    fs.rmSync(dataDir, { recursive: true, force: true });
  }
}

function stopProcessTree(child) {
  return new Promise((resolve) => {
    if (!child.pid || child.exitCode !== null) {
      resolve();
      return;
    }
    const killer =
      process.platform === "win32"
        ? spawn("taskkill", ["/pid", String(child.pid), "/t", "/f"], { windowsHide: true })
        : null;
    if (killer) {
      killer.once("exit", () => resolve());
      killer.once("error", () => {
        child.kill("SIGKILL");
        resolve();
      });
      return;
    }
    child.kill("SIGTERM");
    const timer = setTimeout(() => {
      child.kill("SIGKILL");
      resolve();
    }, 2000);
    child.once("exit", () => {
      clearTimeout(timer);
      resolve();
    });
  });
}

main().catch((error) => fail(error.stack || error.message));
