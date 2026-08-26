_FEATURE_LABELS = {
    "sentence_count": "Sentence count",
    "avg_sentence_length": "Average sentence length",
    "avg_word_length": "Average word length",
    "type_token_ratio": "Vocabulary diversity (type-token ratio)",
}


class ExplanationService:
    """Builds a deterministic, human-readable explanation string.

    No LLM call: the explanation is a template filled in from the score,
    threshold, and stylometric deltas already computed by ScoringService.
    """

    def explain(self, score: float, threshold: float, deltas: dict) -> str:
        headline = (
            f"This submission is {score:.0f}% consistent with the student's "
            f"baseline (flag threshold {threshold:.0f}%)."
        )

        ranked = sorted(
            (
                (self._relative_deviation(values), feature, values)
                for feature, values in deltas.items()
                if feature in _FEATURE_LABELS
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        top = [item for item in ranked if item[0] > 0][:2]
        if not top:
            return headline

        phrases = []
        for index, (_, feature, values) in enumerate(top):
            label = _FEATURE_LABELS[feature]
            comparison = f"{values['submission']:.1f} vs {values['baseline']:.1f}"
            if index == 0:
                phrases.append(f"{label} differs most from the baseline ({comparison})")
            else:
                phrases.append(f"{label} also differs ({comparison})")

        return f"{headline} {'; '.join(phrases)}."

    @staticmethod
    def _relative_deviation(values: dict) -> float:
        baseline = values.get("baseline", 0.0)
        submission = values.get("submission", 0.0)
        if baseline == 0:
            return 0.0 if submission == 0 else float(abs(submission))
        return abs(submission - baseline) / abs(baseline)
