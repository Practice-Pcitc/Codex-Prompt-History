import { expect, test } from "@playwright/test";

test("selects projects, edits favorites, creates templates and opens task context", async ({
  page
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  let settings = {
    enabled: true,
    allProjects: false,
    projects: [] as string[],
    excludedProjects: [],
    redact: true
  };
  const record = {
    id: "record1",
    sessionId: "task1",
    projectName: "sample-project",
    prompt: "Fix sample-project",
    createdAt: "2026-01-01T00:00:00Z",
    source: "codex-local-session"
  };
  let favorite = {
    id: "favorite1",
    kind: "favorite",
    title: "Fix sample-project",
    content: "Fix sample-project",
    tags: [],
    note: "",
    createdAt: record.createdAt
  };
  await page.route("**/api/v1/workbench/**", async (route) => {
    const req = route.request();
    const path = new URL(req.url()).pathname;
    let data: unknown;
    if (path.endsWith("/settings")) {
      if (req.method() === "PUT") settings = req.postDataJSON();
      data = settings;
    } else if (path.endsWith("/status"))
      data = {
        state: settings.projects.length ? "recording" : "waiting",
        sourcePath: "local-test",
        availableProjects: [
          { path: "D:\\sample-project", name: "sample-project" },
          { path: "D:\\another-project", name: "另一个项目" }
        ],
        ignoredLines: 0
      };
    else if (path.endsWith("/overview"))
      data = {
        records: settings.projects.length ? 1 : 0,
        tasks: settings.projects.length ? 1 : 0,
        library: 1,
        projects: settings.projects.length
          ? [
              {
                path: "D:\\sample-project",
                name: "sample-project",
                records: 1,
                tasks: 1,
                lastRecordAt: record.createdAt
              }
            ]
          : []
      };
    else if (path.endsWith("/favorites")) data = favorite;
    else if (path.endsWith("/templates"))
      data = { ...favorite, id: "template1", kind: "template", content: "Fix {{项目名称}}" };
    else if (req.method() === "PUT") {
      favorite = req.postDataJSON();
      data = favorite;
    } else
      data = {
        items: path.endsWith("/tasks")
          ? [{ ...record, title: "Fix sample-project", count: 2 }]
          : path.endsWith("/library")
            ? [favorite]
            : settings.projects.length
              ? [record]
              : [],
        pagination: { total: settings.projects.length ? 1 : 0 }
      };
    await route.fulfill({ json: { data } });
  });
  await page.goto("/prompt-history");
  await page.getByRole("button", { name: "采集设置", exact: true }).click();
  await page.getByText("D:\\sample-project", { exact: true }).click();
  await page.getByRole("button", { name: "保存并同步" }).click();
  await expect(page.getByRole("dialog", { name: "本机采集设置" })).toBeHidden();
  await expect(page.getByRole("button", { name: "Fix sample-project", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /另一个项目/ })).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("workbench.png"),
    fullPage: true,
    animations: "disabled"
  });
  await page.getByRole("button", { name: /打开对话/ }).click();
  await page.getByRole("button", { name: "展开全文" }).click();
  await expect(page.getByRole("dialog", { name: "提问详情" }).locator("pre").first()).toHaveText(
    "Fix sample-project"
  );
  await page
    .getByRole("dialog", { name: "提问详情" })
    .getByRole("button", { name: "关闭", exact: true })
    .click();
  await page.getByRole("button", { name: "收藏", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "编辑收藏 / 模板" })).toBeVisible();
  await page.getByRole("textbox", { name: "标题", exact: true }).fill("有效的修复提问");
  await page.getByRole("button", { name: "保存", exact: true }).click();
  await page.getByRole("button", { name: "收藏与模板", exact: true }).click();
  await expect(page.getByRole("heading", { name: "有效的修复提问" })).toBeVisible();
  await page.getByRole("button", { name: /生成模板/ }).click();
  await expect(page.getByRole("textbox", { name: /内容/ })).toHaveValue("Fix {{项目名称}}");
  await page.getByRole("button", { name: "关闭", exact: true }).click();
  await page.getByRole("button", { name: "对话列表", exact: true }).click();
  await page.getByRole("button", { name: /打开对话/ }).click();
  await expect(page.getByText(/你的提问，按发送顺序/)).toBeVisible();
  await page.getByRole("button", { name: /另一个项目/ }).click();
  await expect(page.getByText("这个项目尚未开启采集")).toBeVisible();
  await page.getByRole("button", { name: "启用这个项目" }).click();
  await expect(page.getByText("这个项目尚未开启采集")).toBeHidden();
  await page.getByRole("button", { name: "暂停记录", exact: true }).click();
  await expect(page.getByRole("button", { name: "恢复记录", exact: true })).toBeVisible();
  expect(errors).toEqual([]);
});
