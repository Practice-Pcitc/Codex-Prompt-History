import { defineStore } from "pinia";

import {
  getCodexSessions,
  getPromptHistory,
  getPromptProjects,
  getPromptRecord,
  getPromptStats,
  getToolEvents
} from "../api/promptApi";
import type {
  CodexSession,
  Pagination,
  PromptFilters,
  PromptProject,
  PromptRecord,
  PromptStats,
  ToolEvent
} from "../types/prompt";

interface PromptState {
  items: PromptRecord[];
  stats: PromptStats;
  projects: PromptProject[];
  sessions: CodexSession[];
  toolEvents: ToolEvent[];
  filters: PromptFilters;
  pagination: Pagination;
  sessionPagination: Pagination;
  toolPagination: Pagination;
  selected: PromptRecord | null;
  loading: boolean;
  sessionsLoading: boolean;
  toolsLoading: boolean;
  detailLoading: boolean;
  error: string | null;
  requests: { list: number; sessions: number; tools: number; detail: number };
}

const emptyStats: PromptStats = {
  totalPromptCount: 0,
  todayPromptCount: 0,
  projectCount: 0,
  recentPromptCount: 0,
  recentDays: 7
};

export const usePromptStore = defineStore("prompt-history", {
  state: (): PromptState => ({
    items: [],
    stats: { ...emptyStats },
    projects: [],
    sessions: [],
    toolEvents: [],
    filters: {},
    pagination: { page: 1, pageSize: 20, total: 0 },
    sessionPagination: { page: 1, pageSize: 20, total: 0 },
    toolPagination: { page: 1, pageSize: 20, total: 0 },
    selected: null,
    loading: false,
    sessionsLoading: false,
    toolsLoading: false,
    detailLoading: false,
    error: null,
    requests: { list: 0, sessions: 0, tools: 0, detail: 0 }
  }),
  actions: {
    async bootstrap() {
      await Promise.all([
        this.loadList(),
        this.loadSessions(),
        this.loadToolEvents(),
        this.loadStats(),
        this.loadProjects()
      ]);
    },
    async loadList() {
      const request = ++this.requests.list;
      this.loading = true;
      this.error = null;
      try {
        const data = await getPromptHistory(
          { ...this.filters },
          this.pagination.page,
          this.pagination.pageSize
        );
        if (request !== this.requests.list) return;
        this.items = data.items;
        this.pagination = data.pagination;
      } catch {
        if (request !== this.requests.list) return;
        this.error = "无法读取 Prompt 历史，请确认 Prompt History 后端已经启动。";
      } finally {
        if (request === this.requests.list) this.loading = false;
      }
    },
    async loadStats() {
      try {
        this.stats = await getPromptStats();
      } catch {
        this.stats = { ...emptyStats };
      }
    },
    async loadProjects() {
      try {
        this.projects = await getPromptProjects();
      } catch {
        this.projects = [];
      }
    },
    async loadSessions() {
      const request = ++this.requests.sessions;
      this.sessionsLoading = true;
      try {
        const data = await getCodexSessions(
          { ...this.filters },
          this.sessionPagination.page,
          this.sessionPagination.pageSize
        );
        if (request !== this.requests.sessions) return;
        this.sessions = data.items;
        this.sessionPagination = data.pagination;
      } catch {
        if (request !== this.requests.sessions) return;
        this.sessions = [];
        this.sessionPagination.total = 0;
        this.error = "无法读取会话记录，请稍后重试。";
      } finally {
        if (request === this.requests.sessions) this.sessionsLoading = false;
      }
    },
    async loadToolEvents() {
      const request = ++this.requests.tools;
      this.toolsLoading = true;
      try {
        const data = await getToolEvents(
          { ...this.filters },
          this.toolPagination.page,
          this.toolPagination.pageSize
        );
        if (request !== this.requests.tools) return;
        this.toolEvents = data.items;
        this.toolPagination = data.pagination;
      } catch {
        if (request !== this.requests.tools) return;
        this.toolEvents = [];
        this.toolPagination.total = 0;
        this.error = "无法读取工具事件，请稍后重试。";
      } finally {
        if (request === this.requests.tools) this.toolsLoading = false;
      }
    },
    async applyFilters(filters: PromptFilters) {
      this.filters = filters;
      this.pagination.page = 1;
      this.sessionPagination.page = 1;
      this.toolPagination.page = 1;
      await Promise.all([this.loadList(), this.loadSessions(), this.loadToolEvents()]);
    },
    async changePage(page: number, pageSize: number) {
      this.pagination.page = page;
      this.pagination.pageSize = pageSize;
      await this.loadList();
    },
    async changeSessionPage(page: number, pageSize: number) {
      this.sessionPagination.page = page;
      this.sessionPagination.pageSize = pageSize;
      await this.loadSessions();
    },
    async changeToolPage(page: number, pageSize: number) {
      this.toolPagination.page = page;
      this.toolPagination.pageSize = pageSize;
      await this.loadToolEvents();
    },
    async openDetail(id: string) {
      const request = ++this.requests.detail;
      this.detailLoading = true;
      this.selected = null;
      this.error = null;
      try {
        const record = await getPromptRecord(id);
        if (request !== this.requests.detail) return;
        this.selected = record;
      } catch {
        if (request !== this.requests.detail) return;
        this.error = "无法读取 Prompt 详情，请稍后重试。";
      } finally {
        if (request === this.requests.detail) this.detailLoading = false;
      }
    },
    closeDetail() {
      this.requests.detail++;
      this.detailLoading = false;
      this.selected = null;
    }
  }
});
