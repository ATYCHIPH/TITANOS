const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "..");
const targets = ["release", "desktop-runtime", "dist"];

for (const target of targets) {
  const fullPath = path.join(root, target);
  fs.rmSync(fullPath, { recursive: true, force: true });
  console.log(`Removed ${fullPath}`);
}
