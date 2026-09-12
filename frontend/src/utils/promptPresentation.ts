/** Remove the client's attachment wrapper for previews only; the original stays intact. */
export function readablePrompt(text = ""): string {
  const marker = /(?:^|\n)## My request:\s*\n/;
  const match = marker.exec(text);
  const body = match ? text.slice(match.index + match[0].length) : text;
  return body.replace(/<image\b[^>]*>[\s\S]*?<\/image>/g, "").trim();
}

export function shortPrompt(text = "", length = 90): string {
  const value = readablePrompt(text)
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, "$1")
    .replace(/https?:\/\/[^\s)\]\p{Script=Han}，。！？；：、]+/gu, (address) => {
      try {
        const url = new URL(address);
        return decodeURIComponent(url.pathname.split("/").filter(Boolean).pop() || url.hostname);
      } catch {
        return address;
      }
    })
    .replace(/\s+/g, " ");
  return value.length > length ? value.slice(0, length) + "…" : value || "含附件的提问";
}

export function localDate(value?: string): string {
  if (!value) return "尚无记录";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "时间未知"
    : new Intl.DateTimeFormat("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false
      }).format(date);
}

export function insideProject(path: string, root: string): boolean {
  const normalize = (value: string) => value.replace(/\\/g, "/").replace(/\/+$/, "").toLowerCase();
  return normalize(path) === normalize(root) || normalize(path).startsWith(normalize(root) + "/");
}
