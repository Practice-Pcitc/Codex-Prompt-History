import { expect, test } from "@playwright/test";

test("automatically lists projects and keeps conversations separate", async ({ page }) => {
  const projects = ["Alpha", "Beta"].map((name) => ({
    name,
    path: `D:\\${name}`,
    records: 2,
    tasks: 2,
    lastRecordAt: "2026-01-01T00:00:00Z"
  }));
  await page.route("**/api/v1/workbench/**", async (route) => {
    const url = new URL(route.request().url());
    const endpoint = url.pathname.split("/").pop();
    const project = url.searchParams.get("project");
    let data: unknown;
    if (endpoint === "settings")
      data = { enabled: true, allProjects: true, projects: [], excludedProjects: [], redact: true };
    else if (endpoint === "status")
      data = {
        state: "recording",
        sourcePath: "local",
        availableProjects: projects,
        ignoredLines: 0
      };
    else if (endpoint === "overview") data = { records: 4, tasks: 4, library: 0, projects };
    else if (endpoint === "tasks") {
      const selected = projects.filter((p) => !project || p.path === project);
      const items = selected.flatMap((p) =>
        [1, 2].map((n) => ({
          sessionId: `${p.name}-${n}`,
          title: `${p.name} 对话 ${n}`,
          workingDirectory: p.path,
          projectName: p.name,
          count: 1
        }))
      );
      data = { items, pagination: { total: items.length } };
    } else {
      expect(url.searchParams.get("session_id")).toBe("Alpha-2");
      expect(project).toBe("D:\\Alpha");
      expect(url.searchParams.get("hide_brief")).toBe("false");
      data = {
        items: [
          {
            id: "m1",
            sessionId: "Alpha-2",
            prompt: "继续",
            projectName: "Alpha",
            workingDirectory: "D:\\Alpha"
          }
        ],
        pagination: { total: 1 }
      };
    }
    await route.fulfill({ json: { data } });
  });
  await page.goto("/prompt-history");
  await expect(page.locator(".connection")).toHaveText("正在记录 2 个项目");
  await page.locator(".project-item").filter({ hasText: "Alpha" }).click();
  await expect(page.getByRole("button", { name: "Alpha 对话 1", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Alpha 对话 2", exact: true }).click();
  await expect(page.locator(".conversation-prompt")).toHaveText("继续");
  await expect(page.getByRole("heading", { name: "Alpha", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "← 返回本项目对话列表" }).click();
  await expect(page.getByRole("button", { name: "Alpha 对话 1", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Beta 对话 1", exact: true })).toHaveCount(0);
});
