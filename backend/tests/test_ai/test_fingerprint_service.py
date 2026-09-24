from ai.features.registry import EXTRACTOR_VERSION, SCHEMA_VERSION
from ai.fingerprint_service import FingerprintService


def test_extract_returns_the_versioned_v2_shape() -> None:
    result = FingerprintService().extract("The cat sat on the mat. It was warm.")

    assert result["schema_version"] == SCHEMA_VERSION
    assert result["extractor_version"] == EXTRACTOR_VERSION
    assert set(result) == {
        "schema_version",
        "extractor_version",
        "meta",
        "scalars",
        "counts",
        "distributions",
    }


def test_extract_reports_document_shape() -> None:
    result = FingerprintService().extract("One sentence here.\n\nAnd a second one.")

    assert result["meta"]["sentence_count"] == 2
    assert result["meta"]["paragraph_count"] == 2
    assert result["meta"]["paragraphs_reliable"] is True


def test_single_block_text_is_marked_unreliable_for_paragraphs() -> None:
    """A pasted submission that lost its blank lines must not be scored as
    though it had one enormous paragraph."""
    result = FingerprintService().extract("All on one line. No breaks at all here.")

    assert result["meta"]["paragraphs_reliable"] is False


def test_extract_handles_empty_content() -> None:
    result = FingerprintService().extract("")

    assert result["meta"]["word_count"] == 0
    assert result["scalars"] == {}
    assert result["counts"] == {}


def test_extract_handles_content_without_sentence_terminators() -> None:
    result = FingerprintService().extract("no terminator anywhere in this text")

    assert result["meta"]["sentence_count"] == 1
    assert result["meta"]["word_count"] == 6


def test_function_word_frequencies_are_stored_for_later_recomputation() -> None:
    result = FingerprintService().extract("The cat sat on the mat and it was warm.")

    frequencies = result["distributions"]["function_word_freqs"]
    assert frequencies["the"] > 0
    assert frequencies["and"] > 0


def test_baseline_vocabulary_suppresses_known_words() -> None:
    """A recurring name shouldn't be counted as a fresh spelling error on
    every submission the student makes."""
    service = FingerprintService()
    text = "The zorblax device performed adequately during the extended trial."

    without = service.extract(text)["counts"]["spelling_errors"]
    with_vocab = service.extract(text, baseline_vocabulary={"zorblax"})["counts"][
        "spelling_errors"
    ]

    assert with_vocab <= without


def test_vocabulary_returns_lowercased_words() -> None:
    assert FingerprintService.vocabulary("The Cat SAT") == {"the", "cat", "sat"}
