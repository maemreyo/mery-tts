import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, "../../..");
const consoleRoot = resolve(__dirname, "..");
const designFile = resolve(repoRoot, "docs/console/DESIGN.md");
const themeFile = resolve(consoleRoot, "src/theme.css");

function buildThemeCss(tailwindOutput) {
  return `@import "tailwindcss";

/* ─── Generated from docs/console/DESIGN.md ──────────────────────────────────
   This file is authoritative for design tokens.
   Run: pnpm generate:design
   Do not hand-edit — edit DESIGN.md instead.
   ─────────────────────────────────────────────────────────────────────── */

${tailwindOutput}

/* Compatibility aliases for Console runtime CSS. */
@theme {
  --layout-sidebar-w: 220px;
  --layout-topbar-h: 56px;
  --font-sans: var(--font-body-md);
  --font-mono: ui-monospace, "Cascadia Code", "Fira Code", monospace;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.5);
}
`;
}

const result = spawnSync(
  "pnpm",
  ["exec", "design.md", "export", designFile, "--format", "css-tailwind"],
  { cwd: consoleRoot, encoding: "utf-8" },
);

if (result.error || result.status !== 0) {
  console.error(
    "Failed to export DESIGN.md tokens:",
    result.stderr || result.error?.message,
  );
  process.exit(1);
}

const tailwindOutput = result.stdout.trim();
if (!tailwindOutput.startsWith("@theme {")) {
  console.error("Unexpected output from design.md export:\n", tailwindOutput);
  process.exit(1);
}

const expectedTheme = buildThemeCss(tailwindOutput);
const actualTheme = readFileSync(themeFile, "utf-8");

if (actualTheme !== expectedTheme) {
  console.error(
    "theme.css is stale or inconsistent with DESIGN.md. Run: pnpm generate:design",
  );
  process.exit(1);
}

console.log("theme.css tokens are fresh and consistent with DESIGN.md");
