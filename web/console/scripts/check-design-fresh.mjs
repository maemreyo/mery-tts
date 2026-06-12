import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, "../../..");
const designFile = resolve(repoRoot, "docs/console/DESIGN.md");
const themeFile = resolve(__dirname, "../src/theme.css");

const designContent = readFileSync(designFile, "utf-8");
const themeContent = readFileSync(themeFile, "utf-8");

// Verify theme.css contains required token categories
const requiredTokens = [
  "--color-bg-base",
  "--color-bg-surface",
  "--color-bg-raised",
  "--color-accent",
  "--color-success",
  "--color-warning",
  "--color-error",
  "--spacing-md",
  "--radius-md",
  "--font-sans",
];

const missing = requiredTokens.filter((token) => !themeContent.includes(token));
if (missing.length > 0) {
  console.error(`theme.css is missing tokens for: ${missing.join(", ")}`);
  process.exit(1);
}

// Verify theme.css references DESIGN.md
if (!themeContent.includes("Generated from docs/console/DESIGN.md")) {
  console.error("theme.css header is missing DESIGN.md reference; regenerate with pnpm generate:design");
  process.exit(1);
}

// Verify DESIGN.md colors match theme.css (basic consistency check)
const designColors = [
  ["bg-base", /bg-base:\s*"([^"]+)"/, "--color-bg-base:\\s*([^;]+)"],
  ["accent", /accent:\s*"([^"]+)"/, "--color-accent:\\s*([^;]+)"],
  ["success", /success:\s*"([^"]+)"/, "--color-success:\\s*([^;]+)"],
];

const mismatches = [];
for (const [name, designRegex, themeRegex] of designColors) {
  const designMatch = designContent.match(designRegex);
  const themeMatch = themeContent.match(new RegExp(themeRegex));
  if (!designMatch || !themeMatch) {
    mismatches.push(`${name}: missing from DESIGN.md or theme.css`);
    continue;
  }
  if (designMatch[1] !== themeMatch[1]) {
    mismatches.push(`${name}: DESIGN.md has ${designMatch[1]}, theme.css has ${themeMatch[1]}`);
  }
}

if (mismatches.length > 0) {
  console.error(`theme.css is stale or inconsistent with DESIGN.md:\n  - ${mismatches.join("\n  - ")}`);
  process.exit(1);
}

console.log("theme.css tokens are fresh and consistent with DESIGN.md");