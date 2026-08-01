import { describe, it, expect } from "vitest";
import { formatScore, formatPercentage, formatDate } from "@/utils/formatters";

describe("formatScore", () => {
  it("converts 0.85 to 85.0%", () => {
    expect(formatScore(0.85)).toBe("85.0%");
  });

  it("converts 1.0 to 100.0%", () => {
    expect(formatScore(1.0)).toBe("100.0%");
  });

  it("converts 0 to 0.0%", () => {
    expect(formatScore(0)).toBe("0.0%");
  });
});

describe("formatPercentage", () => {
  it("keeps a 0-100 value on its own scale", () => {
    expect(formatPercentage(97.7468)).toBe("97.7%");
  });

  it("formats 100 as 100.0%", () => {
    expect(formatPercentage(100)).toBe("100.0%");
  });

  it("does not multiply, unlike formatScore", () => {
    // The analysis API mixes scales; confusing the two would turn a 97.7
    // consistency score into "9770.0%".
    expect(formatPercentage(97.7)).toBe("97.7%");
    expect(formatScore(97.7)).toBe("9770.0%");
  });
});

describe("formatDate", () => {
  it("formats an ISO date string", () => {
    const result = formatDate("2024-01-15T00:00:00.000Z");
    expect(result).toContain("2024");
    expect(result).toContain("Jan");
  });
});
