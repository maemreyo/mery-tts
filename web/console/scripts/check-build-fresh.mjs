import { readdir, readFile } from "node:fs/promises";

const packagedIndex = await readFile("../../src/mery_tts/console/index.html", "utf-8");
const packageJson = await readFile("package.json", "utf-8");
const assetNames = await readdir("../../src/mery_tts/console/assets");

if (!packageJson.includes("console-check")) {
  console.error("Console package is missing the console-check script.");
  process.exit(1);
}

const scriptMatch = packagedIndex.match(/\/console\/assets\/[^\"]+\.js/);
const styleMatch = packagedIndex.match(/\/console\/assets\/[^\"]+\.css/);
if (!scriptMatch || !styleMatch) {
  console.error("Packaged console index must reference Vite assets under /console/assets/.");
  process.exit(1);
}

const referencedAssets = [scriptMatch[0], styleMatch[0]].map((assetPath) =>
  assetPath.replace("/console/assets/", ""),
);
const missingAssets = referencedAssets.filter((assetName) => !assetNames.includes(assetName));
if (missingAssets.length > 0) {
  console.error(`Packaged console references missing assets: ${missingAssets.join(", ")}`);
  process.exit(1);
}
