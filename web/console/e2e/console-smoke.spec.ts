import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("packaged console exposes the main user-mode landmarks", async ({ page }) => {
  await page.goto("/console");
  await expect(page.getByRole("heading", { name: /Mery Console/i })).toBeVisible();
  await expect(page.getByRole("textbox", { name: /Bearer token/i })).toBeVisible();
  await expect(page.getByRole("navigation", { name: /User Mode navigation/i })).toBeVisible();
  await expect(page.getByRole("region", { name: /Voices/i })).toBeVisible();
});

test("@a11y packaged console has no serious accessibility violations", async ({ page }) => {
  await page.goto("/console");
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(results.violations.filter((violation) => violation.impact === "serious" || violation.impact === "critical")).toEqual([]);
});
