const fs = require("node:fs");
const path = require("node:path");

const coreRoot = path.resolve(__dirname, "..", "..");
const workspaceRoot = path.resolve(coreRoot, "..");
const sourceDir = path.join(workspaceRoot, "titanos-ui", "dist");
const targetDir = path.join(coreRoot, "desktop-ui");

if (!fs.existsSync(path.join(sourceDir, "index.html"))) {
  throw new Error(`Built React UI not found at ${sourceDir}. Run npm run ui:build first.`);
}

fs.rmSync(targetDir, { recursive: true, force: true });
fs.cpSync(sourceDir, targetDir, { recursive: true });

console.log(`Staged TITANOS React UI: ${targetDir}`);
