<script setup lang="ts">
import type { useWorkbench } from "../composables/useWorkbench";
import { readablePrompt, localDate } from "../utils/promptPresentation";
const props = defineProps<{ model: ReturnType<typeof useWorkbench> }>();
const w = props.model;
const {
  settings,
  status,
  settingsOpen,
  editor,
  tagsText,
  excludedText,
  copyEntry,
  variables,
  detail
} = w;
</script>
<template>
  <el-dialog v-model="settingsOpen" title="本机采集设置" width="min(760px, 94vw)">
    <p>
      默认自动记录本机所有项目的用户提问，每 5 秒同步，新项目自动加入并补录历史。
      无需打开本项目文件夹，但后端必须运行。
    </p>
    <p>来源：{{ status.sourcePath }}。会话文件格式变化可能影响采集。</p>
    <el-checkbox v-model="settings.allProjects">自动记录所有项目（含以后新增的项目）</el-checkbox>
    <el-checkbox-group
      v-if="!settings.allProjects"
      v-model="settings.projects"
      class="project-options"
      ><el-checkbox
        v-for="p in status.availableProjects"
        :key="p.path"
        :label="p.path"
        :value="p.path"
        >{{ p.path }}</el-checkbox
      ></el-checkbox-group
    >
    <p v-if="!status.availableProjects.length">
      尚未发现项目，请先在本机 Codex 中发送一条消息，再稍后重试。
    </p>
    <p>排除目录（可留空；绝对路径，每行一个，优先于自动记录）</p>
    <el-input v-model="excludedText" type="textarea" :rows="3" />
    <p>
      <el-checkbox v-model="settings.redact">对新入库消息中的常见密码、Token 字段脱敏</el-checkbox>
    </p>
    <p>
      脱敏不能识别所有敏感内容，请勿选择不应记录的项目。暂停期间的消息恢复后不会补录。取消勾选不会删除已有记录。
    </p>
    <template #footer
      ><el-button @click="settingsOpen = false">取消</el-button
      ><el-button type="primary" @click="w.saveSettings">保存并同步</el-button></template
    >
  </el-dialog>
  <el-dialog
    :model-value="!!editor"
    title="编辑收藏 / 模板"
    width="min(760px, 94vw)"
    @close="editor = null"
  >
    <el-form v-if="editor" label-position="top"
      ><el-form-item label="标题"><el-input v-model="editor.title" maxlength="160" /></el-form-item
      ><el-form-item label="内容（模板变量写作双花括号，例如：项目路径）"
        ><el-input
          v-model="editor.content"
          type="textarea"
          :rows="12"
          maxlength="100000" /></el-form-item
      ><el-form-item label="标签，用逗号分隔"><el-input v-model="tagsText" /></el-form-item
      ><el-form-item label="为什么有效 / 适用场景"
        ><el-input v-model="editor.note" type="textarea" maxlength="2000" /></el-form-item
    ></el-form>
    <p>修改的是独立副本，原始记录不变。生成模板后请检查需替换的内容，可手动补充变量。</p>
    <template #footer
      ><el-button @click="editor = null">关闭</el-button
      ><el-button type="primary" @click="w.saveEditor">保存</el-button></template
    >
  </el-dialog>
  <el-dialog
    :model-value="!!copyEntry"
    title="填写模板变量"
    width="min(600px, 94vw)"
    @close="copyEntry = null"
    ><el-form label-position="top"
      ><el-form-item v-for="(_, name) in variables" :key="name" :label="name"
        ><el-input v-model="variables[name]" /></el-form-item></el-form
    ><template #footer
      ><el-button type="primary" @click="w.copyTemplate">复制填写后的提示词</el-button></template
    ></el-dialog
  >

  <el-dialog
    :model-value="!!detail"
    title="提问详情"
    width="min(860px, 94vw)"
    @close="detail = null"
  >
    <template v-if="detail">
      <p>{{ detail.projectName }} · {{ localDate(detail.createdAt) }}</p>
      <pre class="full-prompt">{{
        readablePrompt(detail.prompt) || "这条消息包含附件，请在原对话中查看。"
      }}</pre>
      <details>
        <summary>原始记录与来源</summary>
        <p>{{ detail.workingDirectory }}</p>
        <p>任务编号：{{ detail.sessionId }}</p>
        <pre class="full-prompt">{{ detail.prompt }}</pre>
      </details>
    </template>
    <template #footer
      ><el-button @click="detail = null">关闭</el-button
      ><el-button v-if="detail" @click="w.copy(detail)">复制原文</el-button
      ><el-button v-if="detail" type="primary" @click="w.favorite(detail)"
        >收藏这条提问</el-button
      ></template
    >
  </el-dialog>
</template>
<style scoped>
.project-options {
  display: flex;
  flex-direction: column;
  max-height: 300px;
  overflow: auto;
  border: 1px solid var(--el-border-color);
  padding: 12px;
  border-radius: 8px;
}
.project-options :deep(.el-checkbox) {
  height: auto;
  margin: 8px 0;
  white-space: normal;
}
.project-options :deep(.el-checkbox__label) {
  white-space: normal;
  overflow-wrap: anywhere;
}
.full-prompt {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font: inherit;
  line-height: 1.8;
  max-height: 60vh;
  overflow: auto;
}
details {
  margin-top: 24px;
  color: var(--el-text-color-secondary);
}
p {
  line-height: 1.7;
}
</style>
