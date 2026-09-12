import { expect, test } from "@playwright/test";

test("loads history, opens a prompt, filters and switches tabs", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const record = {
    id: "sample",
    projectName: "sample-project",
    prompt: "synthetic prompt",
    promptLength: 16,
    createdAt: "2026-01-01T00:00:00Z",
    sessionId: "session-1",
    workingDirectory: "sample",
    source: "test",
    model: "test"
  };
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    let data: unknown;
    if (url.pathname.endsWith("/stats"))
      data = {
        totalPromptCount: 1,
        todayPromptCount: 0,
        projectCount: 1,
        recentPromptCount: 1,
        recentDays: 7
      };
    else if (url.pathname.endsWith("/projects")) data = [];
    else if (url.pathname.endsWith("/sample")) data = record;
    else
      data = {
        items: url.pathname.endsWith("/prompt-history") ? [record] : [],
        pagination: {
          page: 1,
          pageSize: 20,
          total: url.pathname.endsWith("/prompt-history") ? 1 : 0
        }
      };
    await route.fulfill({ json: { data } });
  });
  await page.goto("/diagnostics");
  await expect(page.getByText("synthetic prompt", { exact: true })).toBeVisible();
  await page.getByText("synthetic prompt", { exact: true }).click();
  await expect(page.getByRole("heading", { name: "Prompt 详情" })).toBeVisible();
  await expect(page.locator("pre")).toHaveText("synthetic prompt");
  await page.keyboard.press("Escape");
  await page.getByPlaceholder("搜索 Prompt 原文").fill("synthetic");
  const request = page.waitForRequest((req) => req.url().includes("keyword=synthetic"));
  await page.getByRole("button", { name: "查询", exact: true }).click();
  await request;
  await page.getByRole("tab", { name: /Codex 会话/ }).click();
  await expect(page.getByText("还没有 Codex 会话记录", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: /工具调用/ }).click();
  await expect(page.getByText("还没有工具调用记录", { exact: true })).toBeVisible();
  expect(errors).toEqual([]);
});
