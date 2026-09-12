import { client } from "./client";

export interface Settings {
  enabled: boolean;
  allProjects: boolean;
  projects: string[];
  excludedProjects: string[];
  redact: boolean;
}
export interface Status {
  state: string;
  sourcePath: string;
  lastScanAt?: string;
  lastRecordAt?: string;
  error?: string;
  ignoredLines: number;
  excludedSessions?: number;
  cleanedRecords?: number;
  availableProjects: { path: string; name: string }[];
}
export interface Entry {
  id: string;
  sessionId?: string;
  prompt?: string;
  projectName?: string;
  workingDirectory?: string;
  createdAt?: string;
  updatedAt?: string;
  source?: string;
  favoriteId?: string;
  title?: string;
  content?: string;
  tags?: string[];
  note?: string;
  kind?: string;
  count?: number;
  latestPrompt?: string;
}
export interface Overview {
  records: number;
  tasks: number;
  library: number;
  projects: { path: string; name: string; records: number; tasks: number; lastRecordAt: string }[];
}
export interface Page {
  items: Entry[];
  pagination: { total: number };
}
export const workbenchApi = {
  async get<T>(path: string, params = {}): Promise<T> {
    return (await client.get("/workbench/" + path, { params })).data.data;
  },
  async saveSettings(value: Settings): Promise<Settings> {
    return (await client.put("/workbench/settings", value)).data.data;
  },
  async favorite(id: string): Promise<Entry> {
    return (await client.post(`/workbench/records/${id}/favorites`)).data.data;
  },
  async template(id: string): Promise<Entry> {
    return (await client.post(`/workbench/library/${id}/templates`)).data.data;
  },
  async save(value: Entry): Promise<Entry> {
    return (await client.put(`/workbench/library/${value.id}`, value)).data.data;
  },
  async remove(kind: string, id: string) {
    await client.delete(`/workbench/${kind}/${id}`);
  }
};
