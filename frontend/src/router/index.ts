import { createRouter, createWebHistory } from "vue-router";

import PromptHistory from "../views/PromptHistory.vue";
import Workbench from "../views/Workbench.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/prompt-history" },
    { path: "/prompt-history", component: Workbench },
    { path: "/history", redirect: "/prompt-history" },
    { path: "/diagnostics", component: PromptHistory }
  ]
});
