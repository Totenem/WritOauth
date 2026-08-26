from ai.fingerprint_service import FingerprintService


def test_extract_counts_sentences_and_words() -> None:
    service = FingerprintService()

    result = service.extract("The cat sat. The cat ran fast!")

    assert result["sentence_count"] == 2
    assert result["avg_sentence_length"] == 3.5  # (3 + 4) / 2 words per sentence


def test_extract_computes_average_word_length() -> None:
    service = FingerprintService()

    result = service.extract("cat dog cow")

    assert result["avg_word_length"] == 3.0


def test_extract_type_token_ratio_is_case_insensitive() -> None:
    service = FingerprintService()

    result = service.extract("Cat cat CAT dog.")

    assert result["type_token_ratio"] == 2 / 4


def test_extract_handles_empty_content() -> None:
    service = FingerprintService()

    result = service.extract("   ")

    assert result == {
        "sentence_count": 0,
        "avg_sentence_length": 0.0,
        "avg_word_length": 0.0,
        "type_token_ratio": 0.0,
    }


def test_extract_handles_content_without_sentence_terminators() -> None:
    service = FingerprintService()

    result = service.extract("just some words without punctuation")

    assert result["sentence_count"] == 1
    assert result["avg_sentence_length"] == 5.0
