<script setup lang="ts">
import WorkbenchDialogs from "../components/WorkbenchDialogs.vue";
import { useWorkbench } from "../composables/useWorkbench";
import { shortPrompt, readablePrompt, localDate } from "../utils/promptPresentation";
const w = useWorkbench();
const {
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
  overview,
  projectSearch,
  projectOptions,
  visibleProjects,
  selectedProject,
  detail
} = w;
const states: Record<string, string> = {
  recording: "正在记录",
  waiting: "等待选择项目",
  paused: "已暂停记录",
  missing: "找不到对话来源",
  error: "需要检查采集"
};
</script>
<template>
  <div class="workspace">
    <header class="topbar">
      <a class="brand" href="/prompt-history"
        ><span class="brand-mark">P</span><strong>我的提示词</strong
        ><span class="edition">本地工作台</span></a
      >
      <div class="top-actions">
        <span class="connection" :class="{ ok: status.state === 'recording' }"
          ><i />{{
            status.state === "recording"
              ? `正在记录 ${projectOptions.filter((p) => p.enabled).length} 个项目`
              : states[status.state] || "连接中"
          }}</span
        ><button class="button subtle" @click="w.pause">
          {{ settings.enabled ? "暂停记录" : "恢复记录" }}</button
        ><button class="button" @click="w.openSettings">采集设置</button>
      </div>
    </header>
    <div class="layout">
      <aside class="sidebar" aria-label="项目列表">
        <div class="side-heading">
          <h2>项目</h2>
          <span>{{ projectOptions.length }} 个已发现</span>
        </div>
        <input
          v-model="projectSearch"
          class="input"
          placeholder="查找项目或目录"
          aria-label="查找项目"
        />
        <button
          class="project-item all"
          :class="{ selected: !project }"
          @click="w.selectProject('')"
        >
          <span>全部已保存记录</span><strong>{{ overview.records }}</strong>
        </button>
        <p class="side-caption">项目 → 对话 → 提示词</p>
        <div class="project-list">
          <button
            v-for="p in visibleProjects"
            :key="p.path"
            class="project-item"
            :class="{ selected: project === p.path }"
            :title="p.path"
            @click="w.selectProject(p.path)"
          >
            <span class="project-label">▸ {{ p.name }}</span
            ><span class="project-meta"
              ><span :class="{ enabled: p.enabled }">{{
                p.enabled ? "已开启采集" : "未开启采集"
              }}</span
              ><span>{{ p.tasks }} 个对话 · {{ p.records }} 条</span></span
            >
          </button>
          <p v-if="!visibleProjects.length" class="muted">没有匹配的项目。</p>
        </div>
        <div class="side-note">
          {{ settings.allProjects ? "所有项目自动记录，新项目自动加入。" : "当前仅记录指定项目。"
          }}<br />点击项目，再打开对话查看全部提示词。<br />内部审批、子代理任务不会收集。
        </div>
      </aside>
      <main class="content">
        <section class="intro">
          <div>
            <p class="kicker">找回提问 · 保留经验 · 下次复用</p>
            <h1>{{ selectedProject?.name || "把聊过的问题，变成可复用的经验" }}</h1>
            <p v-if="selectedProject" class="project-path">{{ selectedProject.path }}</p>
            <p v-else class="muted">
              所有项目自动记录。点击左侧项目，再打开对应对话，按时间回看每一条提示词。
            </p>
          </div>
        </section>
        <section v-if="selectedProject && !selectedProject.enabled" class="notice">
          <div>
            <strong>这个项目尚未开启采集</strong>
            <p>这里只显示已有记录。开启后，将导入该目录及子目录的历史用户提问。</p>
          </div>
          <button class="button primary" @click="w.enableProject(selectedProject.path)">
            启用这个项目
          </button>
        </section>
        <section class="metrics" aria-label="记录概览">
          <div>
            <span>{{ selectedProject ? "本项目提问" : "全部已保存提问" }}</span
            ><strong>{{ selectedProject?.records ?? overview.records }}</strong
            ><small>不含内部审批任务</small>
          </div>
          <div>
            <span>{{ selectedProject ? "本项目对话" : "全部对话" }}</span
            ><strong>{{ selectedProject?.tasks ?? overview.tasks }}</strong
            ><small>补充与纠错放在一起</small>
          </div>
          <div>
            <span>已开启采集</span
            ><strong
              >{{ projectOptions.filter((p) => p.enabled).length
              }}<em> / {{ projectOptions.length }}</em></strong
            ><small>{{
              settings.allProjects ? "新项目自动加入，无需逐个启用" : "当前使用指定项目范围"
            }}</small>
          </div>
          <button @click="w.switchTab('library')">
            <span>收藏与模板</span><strong>{{ overview.library }}</strong
            ><small>留下有效的提问方法 →</small>
          </button>
        </section>
        <div class="sync-line">
          <span>{{ states[status.state] }} · 最近扫描 {{ localDate(status.lastScanAt) }}</span
          ><span v-if="status.cleanedRecords"
            >本次已清理 {{ status.cleanedRecords }} 条误收记录</span
          ><span v-else>仅保存在本机</span>
        </div>
        <div v-if="status.error || error" class="error" role="alert">
          {{ error || status.error }}
        </div>
        <section class="record-panel">
          <div class="panel-head">
            <nav aria-label="查看方式">
              <button :class="{ active: tab === 'tasks' }" @click="w.switchTab('tasks')">
                对话列表</button
              ><button :class="{ active: tab === 'records' }" @click="w.switchTab('records')">
                全部提问</button
              ><button :class="{ active: tab === 'library' }" @click="w.switchTab('library')">
                收藏与模板
              </button>
            </nav>
            <span class="result-count"
              >{{ total }} {{ tab === "tasks" ? "个对话" : "条结果" }}</span
            >
          </div>
          <div class="toolbar">
            <input
              v-model="keyword"
              class="input search"
              placeholder="搜索提问内容或关键词…"
              aria-label="搜索提问"
              @keyup.enter="w.search"
            /><template v-if="tab === 'library'"
              ><select v-model="kind" class="input" aria-label="收藏类型" @change="w.search">
                <option value="">收藏和模板</option>
                <option value="favorite">收藏</option>
                <option value="template">模板</option></select
              ><input
                v-model="tag"
                class="input tag-filter"
                placeholder="标签"
                @keyup.enter="w.search" /></template
            ><label v-if="tab === 'records' && !session" class="brief"
              ><input v-model="hideBrief" type="checkbox" @change="w.search" />隐藏“好的 /
              继续”</label
            ><button class="button" @click="w.search">搜索 / 刷新</button>
          </div>
          <div v-if="session" class="timeline-heading">
            <button class="button subtle" @click="w.switchTab('tasks')">← 返回本项目对话列表</button
            ><span>你的提问，按发送顺序 · 包含补充和简短回复</span>
          </div>
          <div v-loading="busy" class="entries">
            <p v-if="busy" role="status">{{ session ? "正在加载对话…" : "正在加载记录…" }}</p>
            <div v-if="!busy && !rows.length && !error" class="empty">
              <div class="empty-symbol">≡</div>
              <h3>
                {{
                  selectedProject && !selectedProject.enabled
                    ? "开启这个项目，就能看到提问"
                    : "这里还没有记录"
                }}
              </h3>
              <p>
                {{
                  keyword
                    ? "尝试其他关键词，或清空筛选条件。"
                    : tab === "library"
                      ? "在提问旁点击“收藏”，把有效的方法留在这里。"
                      : "等待本机对话同步；请检查采集状态和后端是否正在运行。"
                }}
              </p>
            </div>
            <article v-for="(row, index) in rows" :key="row.id || row.sessionId" class="entry">
              <div class="entry-heading">
                <span class="tag">{{
                  row.projectName || (row.kind === "template" ? "可复用模板" : "精选收藏")
                }}</span
                ><span class="date">{{ localDate(row.updatedAt || row.createdAt) }}</span>
              </div>
              <template v-if="tab === 'tasks'">
                <button class="entry-title title-button" @click="w.openTask(row)">
                  {{ shortPrompt(row.title, 110) }}
                </button>
                <p class="excerpt">
                  <span class="muted">最近一条：</span
                  >{{ shortPrompt(row.latestPrompt || row.title, 160) }}
                </p>
                <div class="entry-bottom">
                  <span class="muted">{{ row.count }} 条提问 · 含需求、补充与纠错</span
                  ><button class="button link" @click="w.openTask(row)">打开对话 →</button>
                </div>
              </template>
              <template v-else>
                <button
                  v-if="tab === 'records'"
                  class="entry-title title-button"
                  @click="detail = row"
                >
                  <span v-if="session" class="sequence">{{ (page - 1) * 20 + index + 1 }}.</span
                  >{{ session ? "提示词" : shortPrompt(row.prompt, 160) }}
                </button>
                <pre v-if="tab === 'records' && session" class="conversation-prompt">{{
                  readablePrompt(row.prompt) || "这条消息包含附件，请在原对话中查看。"
                }}</pre>
                <h3 v-else class="entry-title">{{ row.title }}</h3>
                <p v-if="tab === 'library'" class="excerpt">{{ shortPrompt(row.content, 180) }}</p>
                <p v-if="row.note" class="note">使用心得：{{ row.note }}</p>
                <div v-if="row.tags?.length" class="tags">
                  <span v-for="t in row.tags" :key="t">{{ t }}</span>
                </div>
                <div class="entry-bottom">
                  <div class="row-actions">
                    <button class="button subtle" @click="w.copy(row)">
                      {{ row.kind === "template" ? "填写变量并复制" : "复制原文" }}</button
                    ><template v-if="tab === 'records'"
                      ><button class="button subtle" @click="detail = row">展开全文</button
                      ><button class="button subtle" @click="w.favorite(row)">
                        {{ row.favoriteId ? "编辑收藏" : "收藏" }}</button
                      ><button v-if="!session" class="button subtle" @click="w.openTask(row)">
                        查看上下文
                      </button></template
                    ><template v-else
                      ><button class="button subtle" @click="w.edit(row)">编辑</button
                      ><button
                        v-if="row.kind === 'favorite'"
                        class="button link"
                        @click="w.template(row)"
                      >
                        生成模板 →
                      </button></template
                    >
                  </div>
                  <button class="delete" @click="w.remove(row)">删除</button>
                </div>
              </template>
            </article>
          </div>
          <div class="pagination">
            <el-pagination
              v-model:current-page="page"
              :page-size="20"
              :total="total"
              layout="prev, pager, next"
              @current-change="w.load"
            />
          </div>
        </section>
        <footer>主界面只展示你的提问；收藏保留独立副本，原始记录不变。</footer>
      </main>
    </div>
    <WorkbenchDialogs :model="w" />
  </div>
</template>
<style scoped>
.conversation-prompt {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font: inherit;
  line-height: 1.8;
}
.workspace {
  --panel: #141820;
  --line: #292f3c;
  --muted: #9aa7bc;
  --accent: #b5a4ff;
  background: #0c0f15;
  min-height: 100vh;
  color: #e8edf5;
  font:
    14px/1.6 "Segoe UI",
    "Microsoft YaHei",
    sans-serif;
}
* {
  box-sizing: border-box;
}
button,
input,
select {
  font: inherit;
}
button {
  cursor: pointer;
}
button:focus-visible,
a:focus-visible,
input:focus-visible {
  outline: 2px solid #b5a4ff;
  outline-offset: 3px;
}
.topbar {
  min-height: 76px;
  padding: 18px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--line);
  gap: 20px;
  background: #10131a;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: inherit;
}
.brand strong {
  font-size: 19px;
}
.brand-mark {
  display: grid;
  place-items: center;
  background: #8e78ed;
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  width: 36px;
  height: 36px;
  border-radius: 11px;
}
.edition {
  color: var(--muted);
  border-left: 1px solid var(--line);
  padding-left: 12px;
}
.top-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
.connection {
  color: #e1b66b;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 7px;
}
.connection i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}
.connection.ok {
  color: #76d9ae;
}
.layout {
  display: grid;
  grid-template-columns: 270px minmax(0, 1fr);
  max-width: 1800px;
  margin: auto;
}
.sidebar {
  padding: 26px 18px;
  border-right: 1px solid var(--line);
  height: calc(100vh - 76px);
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #10131a;
}
.side-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.side-heading h2 {
  font-size: 16px;
  margin: 0;
}
.side-heading span,
.side-caption {
  font-size: 11px;
  color: var(--muted);
}
.side-caption {
  margin: 0 4px;
}
.input {
  background: #0e121a;
  border: 1px solid #333b4b;
  border-radius: 8px;
  color: #edf1f7;
  padding: 10px 12px;
  min-width: 0;
}
.input::placeholder {
  color: #8390a5;
}
.project-list {
  overflow: auto;
  min-height: 0;
  flex: 1;
}
.project-item {
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  border-radius: 9px;
  background: transparent;
  color: #c3cddd;
  padding: 12px;
  margin-bottom: 5px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.project-item:hover {
  background: #1a2030;
}
.project-item.selected {
  background: #25223b;
  border-color: #554875;
  color: #e0d7ff;
}
.project-item.all {
  flex-direction: row;
  justify-content: space-between;
  flex-shrink: 0;
}
.project-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
  font-weight: 600;
}
.project-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--muted);
}
.project-meta .enabled {
  color: #79d9b0;
}
.side-note {
  border-top: 1px solid var(--line);
  padding-top: 15px;
  color: #a2adc0;
  font-size: 11px;
}
.content {
  padding: 32px 38px 24px;
  max-width: 1300px;
  width: 100%;
  margin: auto;
}
.intro {
  margin-bottom: 24px;
}
.kicker {
  color: #b5a4ff;
  letter-spacing: 2px;
  font-size: 11px;
  margin: 0 0 10px;
}
h1 {
  font-size: 27px;
  line-height: 1.4;
  margin: 0 0 10px;
  overflow-wrap: anywhere;
}
.muted {
  color: var(--muted);
}
.project-path {
  color: var(--muted);
  overflow-wrap: anywhere;
  font-size: 12px;
}
.intro p:last-child {
  margin-bottom: 0;
}
.button {
  border: 1px solid #3a4355;
  background: #1c2330;
  border-radius: 7px;
  color: #dae3f1;
  padding: 8px 13px;
  white-space: nowrap;
}
.button:hover {
  border-color: #9b88dc;
  color: #fff;
}
.button.primary {
  background: #aa93fa;
  border-color: #aa93fa;
  color: #151021;
  font-weight: 600;
}
.button.subtle {
  background: transparent;
  border-color: transparent;
  color: #aebbd0;
}
.button.subtle:hover {
  background: #202736;
}
.button.link {
  border-color: transparent;
  background: transparent;
  color: var(--accent);
}
.notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  background: #24203a;
  border: 1px solid #56487c;
  padding: 16px 20px;
  border-radius: 10px;
  margin-bottom: 20px;
}
.notice p {
  margin: 5px 0 0;
  color: #bcb5d1;
  font-size: 12px;
}
.metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.metrics > div,
.metrics > button {
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 12px;
  padding: 19px;
  text-align: left;
  color: inherit;
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.metrics span {
  font-size: 12px;
  color: #abb6c8;
}
.metrics strong {
  font-size: 29px;
  line-height: 1.3;
  font-weight: 600;
}
.metrics em {
  font-size: 15px;
  color: var(--muted);
  font-style: normal;
}
.metrics small {
  font-size: 10px;
  color: var(--muted);
}
.metrics > button:hover {
  border-color: #8d76d0;
}
.sync-line {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 15px 2px;
  color: #8e9bb1;
  font-size: 11px;
}
.error {
  padding: 15px;
  background: #42222b;
  color: #f1b4bf;
  border-radius: 9px;
  margin-bottom: 15px;
}
.record-panel {
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #11161e;
  overflow: hidden;
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  border-bottom: 1px solid var(--line);
}
nav {
  display: flex;
  gap: 25px;
}
nav button {
  padding: 19px 0 16px;
  border: 0;
  border-bottom: 3px solid transparent;
  background: transparent;
  color: #9cabc0;
  font-weight: 600;
}
nav button.active {
  border-bottom-color: #b3a0ff;
  color: #d2c7ff;
}
.result-count {
  color: #8f9eb3;
  font-size: 12px;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 22px;
  background: #141a24;
}
.search {
  flex: 1;
}
.tag-filter {
  width: 100px;
}
.brief {
  font-size: 11px;
  color: #a8b6ca;
  white-space: nowrap;
}
.brief input {
  accent-color: #af96ff;
}
.timeline-heading {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 10px 15px;
  color: var(--muted);
  font-size: 12px;
  border-bottom: 1px solid var(--line);
}
.entries {
  min-height: 230px;
}
.entry {
  padding: 22px 25px;
  border-bottom: 1px solid #252d3b;
}
.entry:last-child {
  border-bottom: 0;
}
.entry-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.tag {
  padding: 3px 9px;
  background: #252238;
  color: #c0afea;
  border-radius: 5px;
  font-size: 11px;
  max-width: 70%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.date {
  font-size: 11px;
  color: #8695ac;
}
.entry-title {
  font-size: 17px;
  font-weight: 600;
  line-height: 1.7;
  margin: 0;
  color: #e4eaf4;
  overflow-wrap: anywhere;
}
.title-button {
  display: block;
  background: none;
  border: 0;
  padding: 0;
  text-align: left;
}
.title-button:hover {
  color: #c1adff;
}
.excerpt {
  color: #b0bdd0;
  font-size: 13px;
  line-height: 1.8;
  margin: 12px 0 16px;
  overflow-wrap: anywhere;
}
.entry-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
  font-size: 11px;
}
.row-actions {
  display: flex;
  gap: 3px;
  flex-wrap: wrap;
}
.row-actions .button {
  font-size: 12px;
  padding: 5px 8px;
}
.delete {
  background: none;
  border: 0;
  color: #8b95a8;
  font-size: 11px;
  padding: 5px;
}
.delete:hover {
  color: #f29aab;
}
.sequence {
  color: #8f7acb;
  padding-right: 8px;
}
.tags {
  display: flex;
  gap: 7px;
  flex-wrap: wrap;
}
.tags span {
  font-size: 11px;
  background: #263346;
  color: #bbcbe2;
  padding: 2px 7px;
  border-radius: 4px;
}
.note {
  font-size: 12px;
  color: #a7c6b9;
}
.empty {
  text-align: center;
  padding: 45px 20px;
  color: var(--muted);
}
.empty h3 {
  font-size: 16px;
  color: #ced7e5;
}
.empty p {
  font-size: 12px;
}
.empty-symbol {
  font-size: 32px;
  color: #7d719f;
}
.pagination {
  display: flex;
  justify-content: center;
  padding: 18px;
  border-top: 1px solid var(--line);
}
.pagination :deep(.el-pagination) {
  --el-fill-color-blank: transparent;
  --el-text-color-primary: #b5c2d7;
  --el-disabled-bg-color: transparent;
  --el-color-primary: #b4a0ff;
}
footer {
  font-size: 11px;
  color: #7f8ba1;
  margin-top: 19px;
  text-align: center;
}
@media (min-width: 1600px) {
  .content {
    padding: 40px 52px;
  }
  .layout {
    grid-template-columns: 300px minmax(0, 1fr);
  }
  h1 {
    font-size: 31px;
  }
}
@media (max-width: 1050px) {
  .layout {
    grid-template-columns: 220px minmax(0, 1fr);
  }
  .content {
    padding: 25px 20px;
  }
  .metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .edition {
    display: none;
  }
  .toolbar {
    flex-wrap: wrap;
  }
  .brief {
    order: 2;
  }
  h1 {
    font-size: 23px;
  }
}
@media (max-width: 700px) {
  .topbar {
    padding: 16px;
    align-items: flex-start;
    flex-wrap: wrap;
  }
  .top-actions {
    width: 100%;
    justify-content: space-between;
  }
  .layout {
    display: block;
  }
  .sidebar {
    position: static;
    height: auto;
    padding: 18px;
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }
  .project-list {
    max-height: 160px;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 5px;
  }
  .side-note {
    display: none;
  }
  .content {
    padding: 22px 12px;
  }
  .metrics > div,
  .metrics > button {
    padding: 14px;
  }
  .metrics strong {
    font-size: 24px;
  }
  .panel-head {
    padding: 0 14px;
  }
  nav {
    gap: 15px;
  }
  nav button {
    font-size: 12px;
  }
  .result-count {
    display: none;
  }
  .toolbar {
    padding: 14px;
  }
  .entry {
    padding: 18px 16px;
  }
  .entry-title {
    font-size: 16px;
  }
  .notice {
    align-items: flex-start;
    flex-direction: column;
  }
  .sync-line {
    flex-direction: column;
    gap: 4px;
  }
  .entry-bottom {
    align-items: flex-start;
  }
  .timeline-heading {
    flex-wrap: wrap;
  }
}
</style>
