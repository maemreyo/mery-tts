import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, "../../..");
const designFile = resolve(repoRoot, "docs/console/DESIGN.md");
const outFile = resolve(__dirname, "../src/theme.css");

const result = spawnSync("pnpm", ["exec", "design.md", "export", designFile, "--format", "css-tailwind"], {
  cwd: resolve(__dirname, ".."),
  encoding: "utf-8",
});

if (result.error || result.status !== 0) {
  console.error("Failed to export DESIGN.md tokens:", result.stderr || result.error?.message);
  process.exit(1);
}

const tailwindOutput = result.stdout.trim();

if (!tailwindOutput.startsWith("@theme {")) {
  console.error("Unexpected output from design.md export:\n", tailwindOutput);
  process.exit(1);
}

const css = `@import "tailwindcss";

/* ─── Generated from docs/console/DESIGN.md ──────────────────────────────────
   This file is authoritative for design tokens.
   Run: pnpm generate:design
   Do not hand-edit — edit DESIGN.md instead.
   ─────────────────────────────────────────────────────────────────────── */

${tailwindOutput}

`;

mkdirSync(dirname(outFile), { recursive: true });
writeFileSync(outFile, css);
console.log(`Generated ${outFile}`);
console.log(tailwindOutput);
