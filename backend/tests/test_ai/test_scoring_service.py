from ai.features.registry import PROFILE_ORDER
from ai.fingerprint_service import FingerprintService
from ai.profile_engine import aggregate
from ai.scoring_service import ScoringService

_LONG = (
    "Although the review was thorough, several questions remain unanswered; "
    "the panel acknowledged this openly in its summary. It is clear that one "
    "of the most persistent difficulties concerns the funding model, which "
    "has not been revisited for a decade. Consequently the recommendations "
    "should be treated as provisional.\n\n"
    "Furthermore the consultation reached only a narrow group of respondents. "
    "In order to broaden participation, the secretariat proposes a second "
    "round; however no budget has been allocated. Nevertheless the direction "
    "of travel is sensible, and the underlying analysis appears sound enough "
    "to justify proceeding with the next stage of the programme this year.\n\n"
    "Because the earlier pilot was abandoned without explanation, some "
    "scepticism is understandable. In order to rebuild confidence the board "
    "should publish the outstanding correspondence; however it has so far "
    "declined to do so. Even allowing for commercial sensitivity, that "
    "position looks difficult to defend for very much longer. Accordingly "
    "the committee intends to raise the matter again at the autumn meeting, "
    "where a fuller account has been promised by the chair."
)


def _baseline(texts: list[str]) -> dict:
    fingerprint = FingerprintService()
    return aggregate([fingerprint.extract(t) for t in texts])


def test_paper_scored_against_itself_is_near_perfect() -> None:
    fingerprint = FingerprintService()
    baseline = _baseline([_LONG, _LONG, _LONG])

    result = ScoringService().score(fingerprint.extract(_LONG), baseline)

    assert result["overall"]["score"] > 95.0
    assert abs(result["overall"]["z"]) < 0.5


def test_every_profile_is_present_in_the_breakdown() -> None:
    fingerprint = FingerprintService()
    result = ScoringService().score(
        fingerprint.extract(_LONG), _baseline([_LONG, _LONG])
    )

    assert set(result["profiles"]) == set(PROFILE_ORDER)


def test_features_below_their_gate_are_suppressed_not_zeroed() -> None:
    """The old engine computed 0.0 for a missing feature and scored that as a
    deviation. A gated feature must be excluded from the maths instead."""
    fingerprint = FingerprintService()
    result = ScoringService().score(
        fingerprint.extract("Too short."), _baseline([_LONG, _LONG])
    )

    lexical = result["profiles"]["lexical"]
    suppressed = [f for f in lexical["features"] if not f["available"]]
    assert suppressed
    assert all(f["suppressed_reason"] for f in suppressed)


def test_typography_is_suppressed_when_source_formats_differ() -> None:
    """Curly quotes and spacing describe the editor, not the writer. A pasted
    baseline versus an extracted PDF must not be scored on them."""
    fingerprint = FingerprintService()
    baseline = _baseline([_LONG, _LONG])

    result = ScoringService().score(
        fingerprint.extract(_LONG), baseline, same_source_format=False
    )

    typography = [
        f
        for f in result["profiles"]["mechanical"]["features"]
        if f["key"] == "curly_quote_ratio"
    ]
    assert typography
    assert typography[0]["available"] is False
    assert "format" in typography[0]["suppressed_reason"]


def test_typography_is_scored_when_formats_match() -> None:
    fingerprint = FingerprintService()
    result = ScoringService().score(
        fingerprint.extract(_LONG), _baseline([_LONG, _LONG]), same_source_format=True
    )

    typography = [
        f
        for f in result["profiles"]["mechanical"]["features"]
        if f["key"] == "curly_quote_ratio"
    ]
    assert typography[0]["available"] is True


def test_habitual_coverage_is_scored_when_supplied() -> None:
    fingerprint = FingerprintService()
    result = ScoringService().score(
        fingerprint.extract(_LONG), _baseline([_LONG, _LONG]), habitual_coverage=0.2
    )

    habitual = [
        f
        for f in result["profiles"]["stylistic"]["features"]
        if f["key"] == "habitual_ngram_coverage"
    ]
    assert habitual[0]["available"] is True
    # Losing 80% of the student's habitual phrasing is a real deviation.
    assert habitual[0]["z"] < -1.0


def test_features_carry_their_evidence() -> None:
    fingerprint = FingerprintService()
    result = ScoringService().score(
        fingerprint.extract(_LONG), _baseline([_LONG, _LONG])
    )

    scored = [
        f
        for f in result["profiles"]["syntactic"]["features"]
        if f["available"] and f["key"] == "mean_sentence_length"
    ]
    assert scored, "expected mean_sentence_length to be scored"
    feature = scored[0]
    assert feature["submission"] is not None
    assert feature["baseline_mean"] is not None
    assert feature["score"] is not None
