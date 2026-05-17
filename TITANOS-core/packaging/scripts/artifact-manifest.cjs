const fs = require("node:fs");
const crypto = require("node:crypto");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "..");
const releaseDir = path.join(root, "release");
const manifestPath = path.join(releaseDir, "artifact-manifest.json");

function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) return walk(fullPath);
    return [fullPath];
  });
}

function sha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

const artifacts = walk(releaseDir)
  .filter((filePath) => path.basename(filePath) !== path.basename(manifestPath))
  .map((filePath) => ({
    path: path.relative(releaseDir, filePath).replace(/\\/g, "/"),
    bytes: fs.statSync(filePath).size,
    sha256: sha256(filePath),
  }));

fs.mkdirSync(releaseDir, { recursive: true });
fs.writeFileSync(
  manifestPath,
  JSON.stringify({
    generatedAt: new Date().toISOString(),
    product: "TITANOS",
    artifacts,
  }, null, 2),
);

console.log(`Wrote ${manifestPath}`);
