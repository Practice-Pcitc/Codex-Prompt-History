import { beforeEach, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { usePromptStore } from "../../src/stores/promptStore";
import * as api from "../../src/api/promptApi";

vi.mock("../../src/api/promptApi", () => ({
  getPromptHistory: vi.fn(),
  getPromptRecord: vi.fn(),
  getPromptStats: vi.fn(),
  getPromptProjects: vi.fn(),
  getCodexSessions: vi.fn(),
  getToolEvents: vi.fn()
}));
beforeEach(() => {
  setActivePinia(createPinia());
  vi.resetAllMocks();
});

it("resets all pagination and forwards filters to each list", async () => {
  const result = { items: [], pagination: { page: 1, pageSize: 20, total: 0 } };
  vi.mocked(api.getPromptHistory).mockResolvedValue(result);
  vi.mocked(api.getCodexSessions).mockResolvedValue(result);
  vi.mocked(api.getToolEvents).mockResolvedValue(result);
  const store = usePromptStore();
  store.pagination.page = 3;
  store.sessionPagination.page = 4;
  store.toolPagination.page = 5;
  await store.applyFilters({ projectName: "synthetic" });
  for (const call of [api.getPromptHistory, api.getCodexSessions, api.getToolEvents]) {
    expect(call).toHaveBeenCalledWith({ projectName: "synthetic" }, 1, 20);
  }
  expect(store.loading || store.sessionsLoading || store.toolsLoading).toBe(false);
});

it("handles detail failures without leaving the drawer loading", async () => {
  vi.mocked(api.getPromptRecord).mockRejectedValue(new Error("unavailable"));
  const store = usePromptStore();
  await store.openDetail("missing");
  expect(store.detailLoading).toBe(false);
  expect(store.selected).toBeNull();
  expect(store.error).toContain("详情");
});

it("reports session load failures", async () => {
  vi.mocked(api.getCodexSessions).mockRejectedValue(new Error("unavailable"));
  const store = usePromptStore();
  await store.loadSessions();
  expect(store.sessionsLoading).toBe(false);
  expect(store.error).toContain("会话");
});

it("does not replace a newer list with an older response", async () => {
  let finishFirst!: (value: {
    items: [];
    pagination: { page: number; pageSize: number; total: number };
  }) => void;
  vi.mocked(api.getPromptHistory).mockImplementationOnce(
    () =>
      new Promise((resolve) => {
        finishFirst = resolve;
      })
  );
  vi.mocked(api.getPromptHistory).mockResolvedValueOnce({
    items: [],
    pagination: { page: 2, pageSize: 20, total: 25 }
  });
  const store = usePromptStore();
  const first = store.loadList();
  store.pagination.page = 2;
  await store.loadList();
  finishFirst({ items: [], pagination: { page: 1, pageSize: 20, total: 10 } });
  await first;
  expect(store.pagination.page).toBe(2);
  expect(store.pagination.total).toBe(25);
});
