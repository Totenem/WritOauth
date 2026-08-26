import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import ScoreBreakdown from "@/features/analysis/ScoreBreakdown";

const breakdown = {
  vocabulary: 94.7008547008547,
  sentence_structure: 88.63636363636363,
  grammar: 92.4380704041721,
  readability: 91.8321518207036,
  style: 97.74679671587518,
};

describe("ScoreBreakdown", () => {
  it("renders all five categories with readable labels", () => {
    render(<ScoreBreakdown breakdown={breakdown} />);

    expect(screen.getByText("Vocabulary")).toBeDefined();
    expect(screen.getByText("Sentence structure")).toBeDefined();
    expect(screen.getByText("Grammar")).toBeDefined();
    expect(screen.getByText("Readability")).toBeDefined();
    expect(screen.getByText("Style")).toBeDefined();
  });

  it("treats the values as already on a 0-100 scale", () => {
    render(<ScoreBreakdown breakdown={breakdown} />);

    // 94.7008... must render as 94.7%, not 9470.1% (which is what a 0-1
    // formatter would produce).
    expect(screen.getByText("94.7%")).toBeDefined();
    expect(screen.getByText("88.6%")).toBeDefined();
  });

  it("exposes each score as a meter for assistive tech", () => {
    render(<ScoreBreakdown breakdown={breakdown} />);

    const meters = screen.getAllByRole("meter");
    expect(meters).toHaveLength(5);

    const vocabulary = screen.getByRole("meter", { name: "Vocabulary" });
    expect(vocabulary.getAttribute("aria-valuenow")).toBe("95");
    expect(vocabulary.getAttribute("aria-valuemax")).toBe("100");
  });

  it("clamps an out-of-range value into the bar width", () => {
    render(<ScoreBreakdown breakdown={{ ...breakdown, vocabulary: 140 }} />);

    const fill = screen
      .getByRole("meter", { name: "Vocabulary" })
      .querySelector("div") as HTMLElement;
    expect(fill.style.width).toBe("100%");
  });
});
