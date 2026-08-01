import re

_WORD_PATTERN = re.compile(r"[A-Za-z']+")
_SENTENCE_SPLIT_PATTERN = re.compile(r"[.!?]+")


class FingerprintService:
    """Pure-Python stylometric feature extraction.

    Deliberately dependency-free: sentence/word splitting is done with
    regular expressions rather than a heavier NLP library.
    """

    def extract(self, content: str) -> dict:
        text = content.strip()
        words = _WORD_PATTERN.findall(text)

        if not text or not words:
            return {
                "sentence_count": 0,
                "avg_sentence_length": 0.0,
                "avg_word_length": 0.0,
                "type_token_ratio": 0.0,
            }

        sentences = [s for s in _SENTENCE_SPLIT_PATTERN.split(text) if s.strip()]
        if not sentences:
            sentences = [text]

        sentence_word_counts = [len(_WORD_PATTERN.findall(s)) for s in sentences]
        avg_sentence_length = sum(sentence_word_counts) / len(sentence_word_counts)
        avg_word_length = sum(len(w) for w in words) / len(words)

        lowered_words = [w.lower() for w in words]
        type_token_ratio = len(set(lowered_words)) / len(lowered_words)

        return {
            "sentence_count": len(sentences),
            "avg_sentence_length": avg_sentence_length,
            "avg_word_length": avg_word_length,
            "type_token_ratio": type_token_ratio,
        }
