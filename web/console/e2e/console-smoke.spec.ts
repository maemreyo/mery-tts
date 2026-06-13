import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("packaged console exposes the main user-mode landmarks", async ({ page }) => {
  await page.goto("/console");
  await expect(page.getByRole("banner")).toBeVisible();
  await expect(page.getByRole("navigation", { name: /Main navigation/i })).toBeVisible();
  await expect(page.getByRole("region", { name: /Overview/i })).toBeVisible();
});

test("packaged console sidebar navigation responds to clicks", async ({ page }) => {
  await page.goto("/console");
  await page.getByRole("link", { name: /Playground/i }).click();

  await expect(page).toHaveURL(/\/console#playground$/);
  await expect(page.getByRole("region", { name: /Playground/i })).toBeVisible();
  await expect(
    page.getByRole("link", { name: /Playground/i }),
  ).toHaveAttribute("aria-current", "page");
});

test("packaged console voices sort selector stays responsive", async ({ page }) => {
  await page.goto("/console/#voices");
  const sortSelect = page.getByRole("combobox", { name: /Sort voices/i });

  await expect(sortSelect).toBeVisible();
  await sortSelect.selectOption("engine");

  await expect(sortSelect).toHaveValue("engine");
  await expect(page.getByRole("region", { name: /Voices/i })).toBeVisible();
});

test("@a11y packaged console has no serious accessibility violations", async ({ page }) => {
  await page.goto("/console");
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(
    results.violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical",
    ),
  ).toEqual([]);
});
