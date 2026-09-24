"""spaCy pipeline singleton and the parsed-document value object.

Loading `en_core_web_sm` takes ~1.3s, so it is loaded once per process and
cached on the class - the same pattern the old EmbeddingService used for its
ONNX model.

`ner` is excluded: entity recognition is the most expensive component in the
pipeline and nothing in the six profiles uses it. `exclude` (not `disable`)
is deliberate - `disable` still loads the component into memory.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cached_property
from typing import Any

_SPACY_MODEL = "en_core_web_sm"
_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n+")
_SINGLE_NEWLINE = re.compile(r"\n+")

# Cap on characters handed to spaCy. The parser is O(n) but a pathological
# paste shouldn't be able to stall a request thread.
MAX_CHARS = 200_000


class SpacyPipeline:
    """Lazily-loaded, process-wide spaCy pipeline."""

    _nlp: Any = None

    @classmethod
    def get(cls) -> Any:
        if cls._nlp is None:
            import spacy

            cls._nlp = spacy.load(_SPACY_MODEL, exclude=["ner"])
        return cls._nlp

    @classmethod
    def reset(cls) -> None:
        """Test hook - drops the cached model."""
        cls._nlp = None


@dataclass
class Document:
    """A parsed submission, computed once and shared by all six extractors.

    Extractors must never re-parse: `Document` is the unit of work that makes
    running six feature sets over one essay affordable.
    """

    raw: str
    doc: Any  # spacy.tokens.Doc
    paragraphs: list[str]

    @cached_property
    def sentences(self) -> list[Any]:
        return [s for s in self.doc.sents if s.text.strip()]

    @cached_property
    def words(self) -> list[Any]:
        """Alphabetic tokens only - punctuation, digits and spaces excluded."""
        return [t for t in self.doc if t.is_alpha]

    @cached_property
    def words_lower(self) -> list[str]:
        return [t.text.lower() for t in self.words]

    @cached_property
    def word_count(self) -> int:
        return len(self.words)

    @cached_property
    def sentence_count(self) -> int:
        return len(self.sentences)

    @cached_property
    def paragraph_count(self) -> int:
        return len(self.paragraphs)

    @property
    def paragraphs_reliable(self) -> bool:
        """False when the source lost its blank lines (a plain paste).

        The Discourse profile's paragraph features are suppressed rather than
        computed from a single block, which would otherwise read as a huge
        deviation for a formatting artifact.
        """
        return self.paragraph_count >= 2

    @cached_property
    def sentence_lengths(self) -> list[int]:
        return [len([t for t in s if t.is_alpha]) for s in self.sentences]

    def meta(self) -> dict[str, Any]:
        return {
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "paragraph_count": self.paragraph_count,
            "paragraphs_reliable": self.paragraphs_reliable,
        }


def parse(content: str) -> Document:
    """Parse raw text into a `Document`.

    Paragraphs are split on blank lines, falling back to single newlines so a
    single-spaced document still yields structure.
    """
    text = content.strip()[:MAX_CHARS]
    paragraphs = [p.strip() for p in _PARAGRAPH_SPLIT.split(text) if p.strip()]
    if len(paragraphs) <= 1:
        candidates = [p.strip() for p in _SINGLE_NEWLINE.split(text) if p.strip()]
        if len(candidates) > 1:
            paragraphs = candidates
    if not paragraphs and text:
        paragraphs = [text]

    return Document(raw=text, doc=SpacyPipeline.get()(text), paragraphs=paragraphs)
