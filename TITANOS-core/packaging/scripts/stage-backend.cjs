const fs = require("node:fs");
const crypto = require("node:crypto");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "..");
const exeName = process.platform === "win32" ? "titanos-backend.exe" : "titanos-backend";
const source = path.join(root, "dist", exeName);
const targetDir = path.join(root, "desktop-runtime", "backend");
const target = path.join(targetDir, exeName);
const manifest = path.join(targetDir, "backend-manifest.json");

function sha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

if (!fs.existsSync(source)) {
  throw new Error(`Bundled backend not found at ${source}. Run npm run backend:bundle first.`);
}

fs.rmSync(targetDir, { recursive: true, force: true });
fs.mkdirSync(targetDir, { recursive: true });
fs.copyFileSync(source, target);

if (process.platform !== "win32") {
  fs.chmodSync(target, 0o755);
}

fs.writeFileSync(
  manifest,
  JSON.stringify(
    {
      generatedAt: new Date().toISOString(),
      executable: exeName,
      bytes: fs.statSync(target).size,
      sha256: sha256(target),
    },
    null,
    2,
  ),
);

console.log(`Staged TITANOS backend: ${target}`);
console.log(`Wrote backend manifest: ${manifest}`);
