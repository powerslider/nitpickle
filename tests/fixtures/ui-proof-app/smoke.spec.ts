import { test, expect } from "@playwright/test";

// Phase 0 proof surface: prove the fixture exhibits a clean state and a
// seeded-defect state deterministically, so later ui-proof phases have a stable
// dogfood target. Both tests pass: one asserts the clean flow emits no error
// signal, the other asserts the broken flow emits the seeded signals.

test("clean flow emits no error signals", async ({ page }) => {
  const pageErrors: Error[] = [];
  const serverErrors: number[] = [];
  page.on("pageerror", (e) => pageErrors.push(e));
  page.on("response", (r) => {
    if (r.status() >= 500) serverErrors.push(r.status());
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Home" })).toBeVisible();

  expect(pageErrors).toEqual([]);
  expect(serverErrors).toEqual([]);
});

test("broken flow surfaces the seeded defects", async ({ page }) => {
  const pageErrors: Error[] = [];
  page.on("pageerror", (e) => pageErrors.push(e));

  const boom = page.waitForResponse((r) => r.url().includes("/api/boom"));
  await page.goto("/broken");
  await expect(page.getByRole("heading", { name: "Broken" })).toBeVisible();

  const boomResponse = await boom;
  expect(boomResponse.status()).toBe(500);
  expect(pageErrors.length).toBeGreaterThan(0);
});
