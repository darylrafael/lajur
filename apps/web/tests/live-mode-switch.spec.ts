import { test, expect } from "@playwright/test";

test.describe("Live Mode Gate Switch & UI Verification", () => {
  test("server: /api/token returns 403 when LIVE_MODE_ENABLED is false", async ({ request }) => {
    const response = await request.get("/api/token");
    expect(response.status()).toBe(403);

    const body = await response.json();
    expect(body.error).toBe("Live mode is disabled.");
    expect(body.message).toContain("Live voice sessions are currently disabled");
  });

  test("client: shows visible notice and disables start button in live mode when disabled", async ({
    page,
  }) => {
    // Navigate to live mode (default LIVE_MODE_ENABLED is false)
    await page.goto("/?mode=live");

    // Live disabled notice should be visible in Indonesian
    const notice = page.getByTestId("live-disabled-notice");
    await expect(notice).toBeVisible();
    await expect(notice).toContainText("Suara langsung dinonaktifkan; silakan coba demo replay");

    // The start button should be disabled
    const startButton = page.getByRole("button", { name: /Mulai Sesi Suara/i });
    await expect(startButton).toBeVisible();
    await expect(startButton).toBeDisabled();

    // Toggle to English
    await page.getByRole("button", { name: "EN" }).click();

    // Notice should switch to English
    await expect(notice).toContainText("Live voice is off; try the demo replay");
    const enStartButton = page.getByRole("button", { name: /Start Voice Session/i });
    await expect(enStartButton).toBeVisible();
    await expect(enStartButton).toBeDisabled();

    // Switch to Replay mode: replay still works seamlessly
    await page.getByRole("radio", { name: /Replay/i }).click();
    await expect(page.getByRole("button", { name: /Play Replay/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Play Replay/i })).toBeEnabled();
  });
});
