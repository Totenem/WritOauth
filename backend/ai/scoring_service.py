import math


class ScoringService:
    """Turns embeddings + stylometrics into 0-100 consistency scores.

    No grammar-checker or true syllable-based readability model is part of
    this phase, so `grammar` and `readability` in `score_breakdown` are
    deterministic proxies built from the stylometric fingerprint rather than
    linguistically-grounded measurements. This is a documented limitation,
    not an oversight.
    """

    def score(
        self, submission_vector: list[float], profile_centroid: list[float]
    ) -> float:
        """Cosine similarity between two embeddings, mapped from [-1, 1] to [0, 100]."""
        if not submission_vector or not profile_centroid:
            return 0.0
        if len(submission_vector) != len(profile_centroid):
            return 0.0

        dot = sum(a * b for a, b in zip(submission_vector, profile_centroid))
        norm_a = math.sqrt(sum(a * a for a in submission_vector))
        norm_b = math.sqrt(sum(b * b for b in profile_centroid))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        cosine = max(-1.0, min(1.0, dot / (norm_a * norm_b)))
        return (cosine + 1.0) / 2.0 * 100.0

    def score_breakdown(
        self,
        submission_fingerprint: dict,
        baseline_fingerprint: dict,
        style_score: float,
    ) -> dict:
        """Per-category 0-100 sub-scores matching `schemas.analysis.BreakdownScore`.

        - vocabulary: type-token ratio consistency
        - sentence_structure: average sentence length consistency
        - grammar: average word length consistency (proxy - no real grammar
          checker in this phase)
        - readability: consistency of a simple sentence/word-length
          composite (proxy - no syllable-based Flesch score in this phase)
        - style: the overall embedding cosine similarity (`style_score`)
        """
        return {
            "vocabulary": self._feature_consistency(
                submission_fingerprint.get("type_token_ratio", 0.0),
                baseline_fingerprint.get("type_token_ratio", 0.0),
            ),
            "sentence_structure": self._feature_consistency(
                submission_fingerprint.get("avg_sentence_length", 0.0),
                baseline_fingerprint.get("avg_sentence_length", 0.0),
            ),
            "grammar": self._feature_consistency(
                submission_fingerprint.get("avg_word_length", 0.0),
                baseline_fingerprint.get("avg_word_length", 0.0),
            ),
            "readability": self._feature_consistency(
                self._readability_index(submission_fingerprint),
                self._readability_index(baseline_fingerprint),
            ),
            "style": style_score,
        }

    @staticmethod
    def _readability_index(fingerprint: dict) -> float:
        return 0.6 * fingerprint.get(
            "avg_sentence_length", 0.0
        ) + 0.4 * fingerprint.get("avg_word_length", 0.0)

    @staticmethod
    def _feature_consistency(submission_value: float, baseline_value: float) -> float:
        if baseline_value == 0:
            return 100.0 if submission_value == 0 else 0.0
        relative_deviation = abs(submission_value - baseline_value) / abs(
            baseline_value
        )
        return max(0.0, 100.0 - relative_deviation * 100.0)
