"""Extract plain text from an uploaded document.

The extracted text is all that is kept: no file is written to disk and no
blob column exists. That keeps the deployment stateless and means the
existing `papers.content` column carries everything downstream needs.

One extraction concern matters more than it looks. PDF text extraction
mangles typography - it produces curly quotes, drops ligatures, and leaves
line-break hyphenation ("inter-\\nesting"). Those artifacts feed the
Mechanical profile, so a de-hyphenation pass runs here and the scoring layer
separately suppresses typography features when a submission's source format
differs from the baselines'. Without both, a student would be flagged for
switching from a textarea to a PDF.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

# Extensions we can read. Anything else is refused with a clear message
# rather than being silently decoded as garbage.
PDF = "pdf"
DOCX = "docx"
TEXT = "txt"

_EXTENSION_FORMATS = {
    ".pdf": PDF,
    ".docx": DOCX,
    ".txt": TEXT,
    ".md": TEXT,
    ".markdown": TEXT,
}

SUPPORTED_EXTENSIONS = tuple(sorted(_EXTENSION_FORMATS))

# Joins "inter-\nesting" back into "interesting". Only applied when the two
# halves are lowercase, so a genuine hyphenated compound at a line break
# ("self-\naware") is left alone less often than it is wrongly joined.
_LINE_HYPHEN = re.compile(r"([a-z]{2,})-\s*\n\s*([a-z]{2,})")
_EXCESS_BLANK_LINES = re.compile(r"\n{3,}")
_TRAILING_SPACES = re.compile(r"[ \t]+\n")


class ExtractionError(Exception):
    """Raised for any input we can't turn into text.

    Carries a message written for a teacher, not a developer: "this looks
    like a scanned PDF" is actionable, "0 characters extracted" is not.
    """


@dataclass
class ExtractionResult:
    filename: str
    source_format: str
    text: str
    word_count: int
    page_count: int | None = None
    warnings: list[str] = field(default_factory=list)


def extract_text(filename: str, data: bytes, max_bytes: int) -> ExtractionResult:
    if not data:
        raise ExtractionError("That file is empty.")
    if len(data) > max_bytes:
        raise ExtractionError(
            f"That file is {_megabytes(len(data))} MB, which is over the "
            f"{_megabytes(max_bytes)} MB limit."
        )

    source_format = _format_for(filename)
    if source_format == PDF:
        text, pages, warnings = _from_pdf(data)
    elif source_format == DOCX:
        text, pages, warnings = _from_docx(data)
    else:
        text, pages, warnings = _from_text(data)

    text = _tidy(text)
    word_count = len(text.split())

    if word_count == 0:
        raise ExtractionError(_no_text_message(source_format))

    return ExtractionResult(
        filename=filename,
        source_format=source_format,
        text=text,
        word_count=word_count,
        page_count=pages,
        warnings=warnings,
    )


def _format_for(filename: str) -> str:
    lowered = (filename or "").lower()
    for extension, source_format in _EXTENSION_FORMATS.items():
        if lowered.endswith(extension):
            return source_format
    raise ExtractionError(
        "That file type isn't supported. Upload a "
        + ", ".join(SUPPORTED_EXTENSIONS)
        + " file, or paste the text instead."
    )


def _from_pdf(data: bytes) -> tuple[str, int | None, list[str]]:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(data))
    except PdfReadError as exc:
        raise ExtractionError("That PDF appears to be corrupt or unreadable.") from exc

    if reader.is_encrypted:
        # An empty user password is common and decrypts silently; a real
        # one cannot be recovered.
        try:
            if reader.decrypt("") == 0:
                raise ExtractionError(
                    "That PDF is password-protected. Remove the password and "
                    "try again, or paste the text instead."
                )
        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError(
                "That PDF is password-protected and could not be opened."
            ) from exc

    warnings: list[str] = []
    pages: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # pragma: no cover - defensive, per-page
            warnings.append(f"Page {index} could not be read and was skipped.")

    return "\n\n".join(pages), len(reader.pages), warnings


def _from_docx(data: bytes) -> tuple[str, int | None, list[str]]:
    import docx

    try:
        document = docx.Document(io.BytesIO(data))
    except Exception as exc:
        raise ExtractionError(
            "That Word file could not be read. If it is an older .doc file, "
            "save it as .docx and try again."
        ) from exc

    paragraphs = [p.text for p in document.paragraphs]
    return "\n\n".join(p for p in paragraphs if p.strip()), None, []


def _from_text(data: bytes) -> tuple[str, int | None, list[str]]:
    warnings: list[str] = []
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1", errors="replace")
        warnings.append(
            "This file wasn't valid UTF-8, so some characters may be wrong. "
            "Check the preview before uploading."
        )
    return text, None, warnings


def _tidy(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _LINE_HYPHEN.sub(r"\1\2", text)
    text = _TRAILING_SPACES.sub("\n", text)
    text = _EXCESS_BLANK_LINES.sub("\n\n", text)
    return text.strip()


def _no_text_message(source_format: str) -> str:
    if source_format == PDF:
        return (
            "No text could be read from that PDF. It looks like a scan or a "
            "set of images rather than a text document - try exporting it as "
            "text, or paste the writing in directly."
        )
    return "No text could be read from that file."


def _megabytes(size: int) -> str:
    return f"{size / (1024 * 1024):.1f}"
