import { expect, it } from "vitest";
import { formatTime, formatDuration } from "../../src/utils/format";
it("handles missing or invalid event metadata", () => {
  expect(formatTime(null)).toBe("—");
  expect(formatTime("invalid")).toBe("—");
  expect(formatTime("2026-01-01T00:00:00Z")).not.toBe("—");
  expect(formatDuration(null)).toBe("—");
  expect(formatDuration(Number.NaN)).toBe("—");
  expect(formatDuration(10.6)).toBe("11 ms");
});
