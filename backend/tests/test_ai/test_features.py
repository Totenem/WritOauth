"""Feature extractor behaviour, including the length-invariance property.

The length-invariance test is the highest-value test in this suite: it is
the one that would have caught the `type_token_ratio` bug in the previous
engine, where the same student's long and short essays looked like different
authors purely because of document length.
"""

import pytest

from ai.features import (
    discourse,
    grammatical,
    lexical,
    mechanical,
    stylistic,
    syntactic,
)
from ai.features.pipeline import parse
from ai.features.registry import BY_KEY, FEATURES, SCALAR

# Comfortably longer than the 100-word MATTR window, so the single-length
# document exercises the real formula rather than its short-text fallback.
# Comparing the fallback against the real formula would look like a length
# dependency without being one.
_PROSE = (
    "Although the committee deliberated at length regarding the proposed "
    "regulation, several members expressed reservations. However, it is clear "
    "that one of the most significant obstacles remains unresolved. "
    "Consequently, the chair recommended a further review before any decision "
    "could reasonably be taken by the wider group.\n\n"
    "In addition, the report was criticised for its brevity by two reviewers. "
    "Nevertheless, the recommendations were adopted without amendment, which "
    "surprised nobody who had followed the earlier discussions closely. "
    "Several delegates noted that the underlying evidence had never been "
    "published, although the secretariat promised a supplementary annex.\n\n"
    "Because the consultation period was unusually brief, many stakeholders "
    "submitted nothing at all. Therefore the responses that were received "
    "cannot reasonably be described as representative of the sector. "
    "Furthermore, the analysis omitted three regions entirely, which the "
    "authors concede in a footnote rather than in the summary itself. "
    "Whether that omission was deliberate remains unclear, but it undermines "
    "confidence in the conclusions presented to the board last spring.\n\n"
    "Finally, the appendix contains figures that contradict the main text. "
    "When questioned about this discrepancy, the lead author attributed it to "
    "a transcription error introduced during production. That explanation has "
    "not satisfied the reviewers, who continue to press for a full erratum."
)


def _all_scalars(text: str) -> dict[str, float]:
    document = parse(text)
    merged: dict[str, float] = {}
    for module in (lexical, syntactic, stylistic, discourse):
        merged.update(module.extract(document).scalars)
    merged.update(mechanical.extract(document).scalars)
    return merged


class TestLengthInvariance:
    """Doubling a document must not move a scored feature.

    Any feature that fails this is measuring document length, not the author.
    """

    def test_scalar_features_survive_doubling(self) -> None:
        once = _all_scalars(_PROSE)
        twice = _all_scalars(_PROSE + "\n\n" + _PROSE)

        word_count = parse(_PROSE).word_count
        drifted = {}
        for key, before in once.items():
            spec = BY_KEY.get(key)
            if spec is None or key not in twice:
                continue
            # A feature below its own gate is never scored in production, so
            # holding it to the invariance property would be meaningless.
            if word_count < spec.min_words:
                continue
            # Paragraph shape legitimately changes when a document is
            # concatenated with itself.
            if spec.requires_paragraphs:
                continue
            after = twice[key]
            if abs(before - after) > 0.02 * max(1.0, abs(before)):
                drifted[key] = (before, after)

        assert not drifted, f"length-dependent features: {drifted}"


class TestLexical:
    def test_mattr_is_higher_for_varied_vocabulary(self) -> None:
        varied = _all_scalars(
            "Numerous distinct expressions populate this particular passage, "
            "demonstrating considerable breadth throughout its construction. "
            "Varied terminology prevents monotonous repetition entirely."
        )
        repetitive = _all_scalars(
            "The cat and the cat and the cat and the cat sat. " * 6
        )
        assert varied["mattr_100"] > repetitive["mattr_100"]

    def test_lexical_density_uses_pos_tags(self) -> None:
        """Content words counted from the tagger, not a stoplist complement."""
        dense = _all_scalars("Angry dogs chase frightened cats through dark forests.")
        sparse = _all_scalars("It is the one that we have been in for a while now.")
        assert dense["lexical_density"] > sparse["lexical_density"]


class TestSyntactic:
    def test_detects_passive_voice_from_dependencies(self) -> None:
        passive = syntactic.extract(parse("The report was written by the committee."))
        active = syntactic.extract(parse("The committee wrote the report."))
        assert passive.scalars["passive_rate"] > active.scalars["passive_rate"]

    def test_does_not_flag_adjectival_be(self) -> None:
        """A `be + adjective` regex would misread this as a passive."""
        result = syntactic.extract(
            parse("She was tired. He was interested. They were happy.")
        )
        assert result.scalars["passive_rate"] == 0.0

    def test_embedding_depth_separates_nested_from_flat_prose(self) -> None:
        nested = syntactic.extract(
            parse("The man who lived in the house that Jack built was tired.")
        )
        flat = syntactic.extract(parse("Jack built a house. A man lived there."))
        assert (
            nested.scalars["max_dependency_depth"]
            > flat.scalars["max_dependency_depth"]
        )

    def test_abbreviations_do_not_split_sentences(self) -> None:
        """The old regex splitter broke on `Dr.`, inflating sentence counts."""
        assert parse("Dr. Smith went home. He slept.").sentence_count == 2


class TestGrammatical:
    @pytest.mark.parametrize(
        "text,family",
        [
            ("He have a problem here today.", "subject_verb_agreement"),
            ("They was late again yesterday.", "subject_verb_agreement"),
            ("She ate a apple for lunch.", "article_a_an"),
            ("I saw the the cat outside.", "repeated_word"),
            ("We left early, they were tired.", "comma_splice"),
        ],
    )
    def test_detects_real_errors(self, text: str, family: str) -> None:
        assert grammatical.extract(parse(text)).counts[family] >= 1

    @pytest.mark.parametrize(
        "text",
        [
            "A university student arrived.",
            "She waited an hour for him.",
            "They were late, and we left.",
            "He had had enough of it.",
            "Dr. Smith went home early.",
            "The figure rose by 3.5 percent.",
            "He could access the archive.",
            "The news is good this morning.",
        ],
    )
    def test_does_not_fire_on_correct_prose(self, text: str) -> None:
        """Negative cases carry the weight here: a rule that fires on valid
        English is worse than no rule, because counts are z-scored and false
        positives contribute pure noise variance."""
        counts = grammatical.extract(parse(text)).counts
        assert sum(counts.values()) == 0, f"false positive on {text!r}: {counts}"


class TestMechanical:
    def test_counts_missing_apostrophes(self) -> None:
        result = mechanical.extract(parse("i dont think thats right at all."))
        assert result.counts["apostrophe_omissions"] == 2

    def test_counts_lowercase_personal_pronoun(self) -> None:
        assert (
            mechanical.extract(parse("i went home and i slept.")).counts["lowercase_i"]
            == 2
        )

    def test_ignores_proper_nouns_when_spellchecking(self) -> None:
        """Names are the dominant false positive for a dictionary check."""
        result = mechanical.extract(
            parse("Barack Obama visited Reykjavik last Tuesday.")
        )
        assert result.counts["spelling_errors"] == 0

    def test_finds_homophone_confusions(self) -> None:
        result = mechanical.extract(parse("Their is a problem we could of avoided."))
        assert result.counts["homophone_confusions"] >= 2


class TestDiscourse:
    def test_readability_separates_simple_from_dense_prose(self) -> None:
        simple = discourse.extract(parse("The cat sat. It was warm. We went home."))
        dense = discourse.extract(
            parse(
                "Notwithstanding considerable methodological complications, the "
                "investigation demonstrated substantial correlations between the "
                "variables under examination."
            )
        )
        assert (
            simple.scalars["flesch_reading_ease"] > dense.scalars["flesch_reading_ease"]
        )
        assert dense.scalars["gunning_fog"] > simple.scalars["gunning_fog"]


class TestStylistic:
    def test_contraction_preference_separates_registers(self) -> None:
        casual = stylistic.extract(parse("I don't think it's right. You're wrong."))
        formal = stylistic.extract(parse("I do not think it is right. You are wrong."))
        assert (
            casual.scalars["contraction_preference"]
            > formal.scalars["contraction_preference"]
        )

    def test_habitual_ngrams_need_two_documents(self) -> None:
        """With one paper this would just memorise that document."""
        single = [parse("It is clear that one of the most important points stands.")]
        assert stylistic.habitual_ngrams(single) == []

    def test_habitual_ngrams_require_repetition_across_papers(self) -> None:
        documents = [
            parse("It is clear that one of the most important points stands firm."),
            parse("It is clear that one of the most difficult tasks remains open."),
        ]
        grams = [entry["ngram"] for entry in stylistic.habitual_ngrams(documents)]
        assert "it is clear" in grams


class TestRegistry:
    def test_every_registered_scalar_is_actually_produced(self) -> None:
        produced = set(_all_scalars(_PROSE))
        registered = {
            spec.key
            for spec in FEATURES
            if spec.kind == SCALAR and spec.min_baseline_papers <= 1
        }
        assert (
            registered <= produced
        ), f"declared but never produced: {registered - produced}"

    def test_feature_keys_are_unique(self) -> None:
        assert len(BY_KEY) == len(FEATURES)
