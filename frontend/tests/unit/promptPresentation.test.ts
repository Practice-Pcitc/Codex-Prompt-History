import { describe, expect, it } from "vitest";
import { insideProject, readablePrompt, shortPrompt } from "../../src/utils/promptPresentation";

describe("prompt presentation", () => {
  it("keeps Chinese text adjacent to a link readable", () => {
    const text =
      "修改[https://github.com/example/CallScope](https://github.com/example/CallScope)该怎么做，而且我要保存";
    expect(shortPrompt(text)).toBe("修改CallScope该怎么做，而且我要保存");
    expect(shortPrompt("查看 https://example.com/%E9%A1%B9%E7%9B%AE")).toBe("查看 项目");
    expect(readablePrompt(text)).toBe(text);
  });
  it("keeps link names readable in cards without changing the original", () => {
    const text = "请整理 [https://github.com/example/project](https://github.com/example/project)";
    expect(shortPrompt(text)).toBe("请整理 project");
    expect(readablePrompt(text)).toBe(text);
  });
  it("previews the request while preserving ordinary prose", () => {
    expect(readablePrompt("# Files mentioned\nfile.md\n## My request:\n请整理代码")).toBe(
      "请整理代码"
    );
    const quote = "The following is the Codex agent history — 请解释这句话";
    expect(readablePrompt(quote)).toBe(quote);
    expect(shortPrompt("完整原文不修改", 4)).toBe("完整原文…");
  });
  it("matches project boundaries rather than directory prefixes", () => {
    expect(insideProject("D:\\Code\\app\\child", "d:/code/app")).toBe(true);
    expect(insideProject("D:\\Code\\app-other", "d:/code/app")).toBe(false);
  });
});
