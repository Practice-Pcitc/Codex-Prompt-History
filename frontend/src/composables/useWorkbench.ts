import { computed, onMounted, onUnmounted, ref } from "vue";
import { insideProject } from "../utils/promptPresentation";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  workbenchApi as api,
  type Entry,
  type Page,
  type Settings,
  type Status
} from "../api/workbench";
import type { Overview } from "../api/workbench";

export function useWorkbench() {
  const tab = ref("tasks"),
    keyword = ref(""),
    project = ref(""),
    session = ref(""),
    kind = ref(""),
    tag = ref("");
  const projectSearch = ref(""),
    detail = ref<Entry | null>(null);
  const overview = ref<Overview>({ records: 0, tasks: 0, library: 0, projects: [] });
  const page = ref(1),
    total = ref(0),
    rows = ref<Entry[]>([]),
    hideBrief = ref(false),
    busy = ref(false),
    error = ref("");
  const settings = ref<Settings>({
    enabled: true,
    allProjects: true,
    projects: [],
    excludedProjects: [],
    redact: true
  });
  const status = ref<Status>({
    state: "waiting",
    sourcePath: "",
    availableProjects: [],
    ignoredLines: 0
  });
  const settingsOpen = ref(false),
    editor = ref<Entry | null>(null),
    tagsText = ref(""),
    excludedText = ref("");
  const copyEntry = ref<Entry | null>(null),
    variables = ref<Record<string, string>>({});
  let timer: ReturnType<typeof setInterval> | undefined;
  let generation = 0;
  const projectOptions = computed(() => {
    const result = new Map<
      string,
      { path: string; name: string; records: number; tasks: number; enabled: boolean }
    >();
    for (const item of [...status.value.availableProjects, ...overview.value.projects]) {
      const counts = overview.value.projects.find((p) => p.path === item.path);
      result.set(item.path, {
        ...item,
        records: counts?.records || 0,
        tasks: counts?.tasks || 0,
        enabled:
          (settings.value.allProjects ||
            settings.value.projects.some((root) => insideProject(item.path, root))) &&
          !settings.value.excludedProjects.some((root) => insideProject(item.path, root))
      });
    }
    return [...result.values()].sort(
      (a, b) =>
        Number(b.enabled) - Number(a.enabled) ||
        b.records - a.records ||
        a.name.localeCompare(b.name, "zh-CN")
    );
  });
  const visibleProjects = computed(() =>
    projectOptions.value.filter((p) =>
      (p.name + " " + p.path).toLowerCase().includes(projectSearch.value.toLowerCase())
    )
  );
  const selectedProject = computed(() =>
    projectOptions.value.find((p) => p.path === project.value)
  );
  async function guarded(action: () => Promise<void>) {
    try {
      await action();
    } catch {
      ElMessage.error("操作失败，请检查后端连接或输入内容后重试。");
    }
  }
  async function load() {
    const request = ++generation;
    busy.value = true;
    try {
      const params = {
        page: page.value,
        page_size: 20,
        keyword: keyword.value,
        project: project.value,
        session_id: session.value,
        hide_brief: session.value ? false : hideBrief.value,
        kind: kind.value,
        tag: tag.value
      };
      const result = await api.get<Page>(tab.value, params);
      if (request === generation) {
        rows.value = result.items;
        total.value = result.pagination.total;
        error.value = "";
      }
    } catch {
      if (request === generation) error.value = "后端连接失败。请确认后端仍在运行，然后点击刷新。";
    } finally {
      if (request === generation) busy.value = false;
    }
  }
  async function refreshStatus() {
    try {
      const previous = status.value.lastRecordAt;
      status.value = await api.get<Status>("status");
      overview.value = await api.get<Overview>("overview");
      if (
        previous &&
        previous !== status.value.lastRecordAt &&
        !editor.value &&
        !settingsOpen.value &&
        !detail.value
      )
        void load();
    } catch {
      status.value = { ...status.value, state: "error", error: "无法连接后端，当前采集状态未知。" };
    }
  }
  function search() {
    page.value = 1;
    void load();
  }
  function switchTab(value: string) {
    tab.value = value;
    session.value = "";
    search();
  }
  function selectProject(path: string) {
    project.value = path;
    session.value = "";
    tab.value = "tasks";
    keyword.value = "";
    search();
  }
  async function enableProject(path: string) {
    await guarded(async () => {
      const current = await api.get<Settings>("settings");
      if (current.excludedProjects.some((root) => insideProject(path, root))) {
        ElMessage.warning("该项目在排除范围内，请先在采集设置中调整排除目录。");
        await openSettings();
        return;
      }
      settings.value = await api.saveSettings({
        ...current,
        projects: [...new Set([...current.projects, path])]
      });
      await refreshStatus();
      search();
    });
  }
  function openTask(row: Entry) {
    tab.value = "records";
    session.value = row.sessionId || row.id;
    keyword.value = "";
    project.value = row.workingDirectory || project.value;
    search();
  }
  function edit(row: Entry) {
    editor.value = { ...row, tags: [...(row.tags || [])] };
    tagsText.value = (row.tags || []).join(", ");
  }
  async function favorite(row: Entry) {
    await guarded(async () => {
      edit(await api.favorite(row.id));
      await load();
    });
  }
  async function template(row: Entry) {
    await guarded(async () => {
      edit(await api.template(row.id));
      await load();
    });
  }
  async function saveEditor() {
    await guarded(async () => {
      if (!editor.value) return;
      editor.value.tags = tagsText.value
        .split(/[,，]/)
        .map((s) => s.trim())
        .filter(Boolean);
      await api.save(editor.value);
      editor.value = null;
      await load();
    });
  }
  async function saveSettings() {
    await guarded(async () => {
      settings.value.excludedProjects = excludedText.value
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
      settings.value = await api.saveSettings(settings.value);
      settingsOpen.value = false;
      await refreshStatus();
      search();
    });
  }
  async function pause() {
    await guarded(async () => {
      settings.value = await api.saveSettings({
        ...settings.value,
        enabled: !settings.value.enabled
      });
      await refreshStatus();
    });
  }
  async function openSettings() {
    await guarded(async () => {
      settings.value = await api.get<Settings>("settings");
      excludedText.value = settings.value.excludedProjects.join("\n");
      settingsOpen.value = true;
    });
  }
  async function remove(row: Entry) {
    try {
      await ElMessageBox.confirm(
        tab.value === "library"
          ? "删除此收藏或模板？原始记录会保留。"
          : "从本工具删除这条记录，后续同步不会重新导入。已收藏副本与 Codex 原始会话仍保留。",
        "删除记录",
        { type: "warning" }
      );
    } catch {
      return;
    }
    await guarded(async () => {
      await api.remove(tab.value === "library" ? "library" : "records", row.id);
      await load();
    });
  }
  async function copyText(text: string) {
    await guarded(async () => {
      await navigator.clipboard.writeText(text);
      ElMessage.success("已复制");
    });
  }
  function copy(row: Entry) {
    const text = row.content || row.prompt || "";
    const keys = [...text.matchAll(/\{\{([^{}]+)\}\}/g)].map((m) => m[1]!);
    if (row.kind === "template" && keys.length) {
      variables.value = Object.fromEntries(keys.map((k) => [k, ""]));
      copyEntry.value = row;
    } else void copyText(text);
  }
  async function copyTemplate() {
    if (Object.values(variables.value).some((v) => !v.trim())) {
      ElMessage.warning("请填写所有模板变量");
      return;
    }
    await copyText(
      (copyEntry.value?.content || "").replace(
        /\{\{([^{}]+)\}\}/g,
        (_, key: string) => variables.value[key] || ""
      )
    );
    copyEntry.value = null;
  }
  onMounted(async () => {
    await guarded(async () => {
      settings.value = await api.get<Settings>("settings");
    });
    await Promise.all([refreshStatus(), load()]);
    timer = setInterval(() => {
      void refreshStatus();
    }, 5000);
  });
  onUnmounted(() => {
    clearInterval(timer);
    generation++;
  });
  return {
    overview,
    projectSearch,
    projectOptions,
    visibleProjects,
    selectedProject,
    detail,
    selectProject,
    enableProject,
    tab,
    keyword,
    project,
    session,
    kind,
    tag,
    page,
    total,
    rows,
    hideBrief,
    busy,
    error,
    settings,
    status,
    settingsOpen,
    editor,
    tagsText,
    excludedText,
    copyEntry,
    variables,
    load,
    search,
    switchTab,
    openTask,
    favorite,
    template,
    edit,
    saveEditor,
    saveSettings,
    pause,
    openSettings,
    remove,
    copy,
    copyTemplate
  };
}
