import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import ScoreBreakdown from "@/features/analysis/ScoreBreakdown";
import { makeBreakdown, makeFeature, makeProfile } from "../../fixtures/analysis";

describe("ScoreBreakdown", () => {
  it("renders the AI fingerprint and all six stylometric profiles", () => {
    render(<ScoreBreakdown breakdown={makeBreakdown()} />);

    for (const label of [
      "AI Style Fingerprint",
      "Stylistic",
      "Syntactic",
      "Lexical",
      "Mechanical",
      "Discourse & Complexity",
      "Grammatical",
    ]) {
      expect(screen.getByText(label)).toBeDefined();
    }
  });

  it("treats scores as already on a 0-100 scale", () => {
    const breakdown = makeBreakdown();
    breakdown.profiles.stylistic = makeProfile({
      label: "Stylistic",
      score: 94.7008547,
    });

    render(<ScoreBreakdown breakdown={breakdown} />);

    // 94.7008... must render as 94.7%, not 9470.1% - which is what a 0-1
    // formatter would produce.
    expect(screen.getByText("94.7%")).toBeDefined();
  });

  it("exposes each measured profile as a meter", () => {
    render(<ScoreBreakdown breakdown={makeBreakdown()} />);

    expect(screen.getAllByRole("meter")).toHaveLength(7);
    const stylistic = screen.getByRole("meter", { name: "Stylistic" });
    expect(stylistic.getAttribute("aria-valuenow")).toBe("92");
    expect(stylistic.getAttribute("aria-valuemax")).toBe("100");
  });

  it("clamps an out-of-range score into the bar width", () => {
    const breakdown = makeBreakdown();
    breakdown.profiles.stylistic = makeProfile({ label: "Stylistic", score: 140 });

    render(<ScoreBreakdown breakdown={breakdown} />);

    const fill = screen
      .getByRole("meter", { name: "Stylistic" })
      .querySelector("span") as HTMLElement;
    expect(fill.style.width).toBe("100%");
  });

  it("shows why a profile could not be measured instead of scoring it zero", () => {
    const breakdown = makeBreakdown();
    breakdown.profiles.grammatical = makeProfile({
      label: "Grammatical",
      score: null,
      z: null,
      available: false,
      suppressed_reason: "Needs at least 100 words",
      features: [],
    });

    render(<ScoreBreakdown breakdown={breakdown} />);

    expect(screen.getByText("Needs at least 100 words")).toBeDefined();
    // A suppressed profile has no bar - rendering one at 0% would read as a
    // total mismatch rather than an absence of measurement.
    expect(screen.queryByRole("meter", { name: "Grammatical" })).toBeNull();
  });

  it("reveals the features behind a profile when expanded", async () => {
    const breakdown = makeBreakdown();
    breakdown.profiles.stylistic = makeProfile({
      label: "Stylistic",
      features: [makeFeature({ label: "Function-word usage" })],
    });

    render(<ScoreBreakdown breakdown={breakdown} />);
    expect(screen.queryByText("Function-word usage")).toBeNull();

    await userEvent.click(screen.getByRole("button", { name: /Stylistic/ }));

    expect(screen.getByText("Function-word usage")).toBeDefined();
  });

  it("badges approximate measures so they are not read as hard evidence", async () => {
    const breakdown = makeBreakdown();
    breakdown.profiles.stylistic = makeProfile({
      label: "Stylistic",
      features: [
        makeFeature({ label: "Unrecognised words", measurement: "approximation" }),
      ],
    });

    render(<ScoreBreakdown breakdown={breakdown} />);
    await userEvent.click(screen.getByRole("button", { name: /Stylistic/ }));

    expect(screen.getByText("approx")).toBeDefined();
  });

  it("describes direction for scalars but not for distributions", async () => {
    const breakdown = makeBreakdown();
    breakdown.profiles.stylistic = makeProfile({
      label: "Stylistic",
      features: [
        makeFeature({ key: "a", label: "Pronoun rate", kind: "scalar", z: 2.5 }),
        makeFeature({ key: "b", label: "Comma rate", kind: "scalar", z: -2.5 }),
        // A divergence is always positive, so "higher" would be meaningless.
        makeFeature({
          key: "c",
          label: "Function-word usage",
          kind: "distribution",
          z: 3,
        }),
      ],
    });

    render(<ScoreBreakdown breakdown={breakdown} />);
    await userEvent.click(screen.getByRole("button", { name: /Stylistic/ }));

    expect(screen.getByText("much higher")).toBeDefined();
    expect(screen.getByText("much lower")).toBeDefined();
    expect(screen.getByText("differs sharply")).toBeDefined();
  });

  it("softens the wording for a mild deviation instead of overstating it", async () => {
    // z=1.2 scores ~83% (100*exp(-0.5*(1.2/2)^2)) - a mild wobble just past
    // the "typical" cutoff, not the same thing as z=2.5 above (~61%).
    // Regression: the report said "higher"/"further than usual" identically
    // for both, which made an 83% score read as alarming as a 61% one.
    const breakdown = makeBreakdown();
    breakdown.profiles.stylistic = makeProfile({
      label: "Stylistic",
      features: [makeFeature({ key: "a", label: "Pronoun rate", kind: "scalar", z: 1.2 })],
    });

    render(<ScoreBreakdown breakdown={breakdown} />);
    await userEvent.click(screen.getByRole("button", { name: /Stylistic/ }));

    expect(screen.getByText("slightly higher")).toBeDefined();
  });

  it("badges the neural profile as the AI model", () => {
    render(<ScoreBreakdown breakdown={makeBreakdown()} />);

    expect(screen.getByText("AI model")).toBeDefined();
  });

  it("still renders analyses made before the neural profile existed", () => {
    const breakdown = makeBreakdown();
    delete breakdown.profiles.neural_style;

    render(<ScoreBreakdown breakdown={breakdown} />);

    expect(screen.getAllByRole("meter")).toHaveLength(6);
    expect(screen.queryByText("AI model")).toBeNull();
  });

  it("describes the neural distance one-sidedly", async () => {
    const breakdown = makeBreakdown();
    breakdown.profiles.neural_style = makeProfile({
      label: "AI Style Fingerprint",
      features: [
        makeFeature({
          key: "luar_distance",
          label: "Overall writing fingerprint (LUAR)",
          z: 4,
        }),
      ],
    });

    render(<ScoreBreakdown breakdown={breakdown} />);
    await userEvent.click(screen.getByRole("button", { name: /AI Style Fingerprint/ }));

    expect(screen.getByText("much further than usual")).toBeDefined();
  });

  it("doesn't overstate a mild neural deviation as dramatic", async () => {
    // z=1.2 scores ~83%, same boundary case as the mild scalar test above -
    // this is the exact scenario reported: "further than usual" at 83%.
    const breakdown = makeBreakdown();
    breakdown.profiles.neural_style = makeProfile({
      label: "AI Style Fingerprint",
      score: 83,
      features: [
        makeFeature({
          key: "luar_distance",
          label: "Overall writing fingerprint (LUAR)",
          z: 1.2,
          score: 83,
        }),
      ],
    });

    render(<ScoreBreakdown breakdown={breakdown} />);
    await userEvent.click(screen.getByRole("button", { name: /AI Style Fingerprint/ }));

    expect(screen.getByText("slightly further than usual")).toBeDefined();
    expect(screen.queryByText("much further than usual")).toBeNull();
  });
});
