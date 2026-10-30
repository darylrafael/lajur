import { test, expect } from "@playwright/test";

test.describe("Lajur Web Simulator Smoke Tests", () => {
  test("loads simulator in offline replay mode with full initial layout", async ({ page }) => {
    await page.goto("/?replay=simple");

    // Header & Titles
    await expect(page.locator("h1")).toContainText("Lajur Voice Ordering");
    await expect(page.getByRole("region", { name: /DEMO REPLAY/i })).toBeVisible();

    // Menu Board
    await expect(page.getByRole("tablist", { name: "Menu Categories" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Paket Hemat" })).toBeVisible();

    // Live Transcript Panel (NFR-07 always visible)
    await expect(page.getByRole("heading", { name: /Transkrip Suara Langsung/i })).toBeVisible();
    await expect(page.getByRole("log")).toBeVisible();

    // Cart Panel
    await expect(page.getByRole("heading", { name: /Ringkasan Keranjang Pesanan/i })).toBeVisible();
    await expect(page.getByText(/Keranjang masih kosong/i)).toBeVisible();
  });

  test("toggles language between ID and EN across UI components", async ({ page }) => {
    await page.goto("/?replay=simple");

    // Initially in Indonesian
    await expect(page.getByRole("button", { name: /Putar Replay/i })).toBeVisible();
    await expect(page.getByText(/Papan Menu Drive-thru/i)).toBeVisible();

    // Click EN button
    await page.getByRole("button", { name: "EN", exact: true }).click();

    // Expect English strings
    await expect(page.getByRole("button", { name: /Play Replay/i })).toBeVisible();
    await expect(page.getByText(/Drive-thru Menu Board/i)).toBeVisible();
    await expect(page.getByRole("heading", { name: /Order Cart Summary/i })).toBeVisible();

    // Click ID button
    await page.getByRole("button", { name: "ID", exact: true }).click();
    await expect(page.getByRole("button", { name: /Putar Replay/i })).toBeVisible();
  });

  test("runs replay execution and verifies live transcript and cart updates", async ({ page }) => {
    // Navigate with replay simple scenario
    await page.goto("/?replay=simple");

    // Click "Putar Replay"
    const playButton = page.getByRole("button", { name: /Putar Replay/i });
    await expect(playButton).toBeVisible();
    await playButton.click();

    // Wait for first turn to be processed into transcript history
    const transcriptLog = page.getByRole("log");
    await expect(transcriptLog).toContainText("Pesan burger sapi tunggal", { timeout: 15000 });

    // Verify cart updates with line item and price
    const cartRegion = page.getByRole("region", { name: "" }).filter({ hasText: /Subtotal/i });
    await expect(cartRegion).toContainText("Burger Sapi Tunggal", { timeout: 15000 });
    await expect(cartRegion).toContainText("Rp", { timeout: 15000 });

    // Verify bot reply card updates
    const botReplyCard = page.locator("text=Lajur Bot").first();
    await expect(botReplyCard).toBeVisible();
  });

  test("handles awaiting choice in combo scenario with interactive options", async ({ page }) => {
    await page.goto("/?replay=combo");

    const playButton = page.getByRole("button", { name: /Putar Replay/i });
    await playButton.click();

    // Wait for pending question banner to appear when dialog transitions to awaiting_choice
    const pendingBanner = page.getByRole("alert").filter({ hasText: /Pilihan Wajib/i });
    await expect(pendingBanner).toBeVisible({ timeout: 15000 });
    await expect(pendingBanner).toContainText("Burger Sapi Tunggal");
  });

  test("displays crew handoff escalation banner in handoff scenario", async ({ page }) => {
    await page.goto("/?replay=handoff");

    const playButton = page.getByRole("button", { name: /Putar Replay/i });
    await playButton.click();

    // Wait for handoff alert banner
    const handoffAlert = page.getByRole("alert").filter({ hasText: /Eskalasi Staf Kasir/i });
    await expect(handoffAlert).toBeVisible({ timeout: 15000 });
    await expect(handoffAlert).toContainText("kasir manusia kami");
  });
});
