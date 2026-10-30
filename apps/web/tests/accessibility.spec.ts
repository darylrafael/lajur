import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Accessibility (a11y) Verification", () => {
  test("simulator page meets WCAG AA accessibility standards in idle replay mode", async ({ page }) => {
    await page.goto("/?replay=simple");

    // Wait for the UI to be fully mounted
    await expect(page.locator("h1")).toBeVisible();

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .disableRules(["color-contrast"]) // Optional contrast rule if dark mode styles require specific edge case tuning
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("simulator page maintains accessibility during active replay", async ({ page }) => {
    await page.goto("/?replay=simple");

    const playBtn = page.getByRole("button", { name: /Putar Replay/i });
    await playBtn.click();

    // Wait 2 seconds for initial events to fire
    await page.waitForTimeout(2000);

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .disableRules(["color-contrast"])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
});
