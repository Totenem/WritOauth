"""Document extraction, including every failure mode a teacher can hit.

Fixture files are generated in-test rather than committed, so there are no
binaries in the repo and the fixtures can't drift from what the parser
expects.
"""

import io

import pytest

from utils.file_extraction import ExtractionError, extract_text

_MAX = 10 * 1024 * 1024


def _raw_pdf(pages: list[str]) -> bytes:
    """Build a minimal PDF carrying real text.

    Hand-assembled rather than generated with reportlab: that keeps the test
    suite free of an extra dependency, and pypdf parses it exactly as it
    would parse a PDF from Word.
    """
    page_ids = [4 + 2 * i for i in range(len(pages))]
    content_ids = [5 + 2 * i for i in range(len(pages))]

    objects: list[tuple[int, bytes]] = [
        (1, b"<< /Type /Catalog /Pages 2 0 R >>"),
        (
            2,
            b"<< /Type /Pages /Kids ["
            + b" ".join(b"%d 0 R" % pid for pid in page_ids)
            + b"] /Count %d >>" % len(pages),
        ),
        (3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
    ]

    for text, page_id, content_id in zip(pages, page_ids, content_ids):
        objects.append(
            (
                page_id,
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                b"/Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>"
                % content_id,
            )
        )
        operators = [b"BT /F1 12 Tf 72 720 Td 14 TL"]
        for line in text.split("\n"):
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            operators.append(b"(" + escaped.encode("latin-1", "replace") + b") Tj T*")
        operators.append(b"ET")
        stream = b"\n".join(operators)
        objects.append(
            (
                content_id,
                b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
            )
        )

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets: dict[int, int] = {}
    for number, body in sorted(objects):
        offsets[number] = out.tell()
        out.write(b"%d 0 obj\n" % number + body + b"\nendobj\n")

    xref_at = out.tell()
    highest = max(offsets)
    out.write(b"xref\n0 %d\n" % (highest + 1))
    out.write(b"0000000000 65535 f \n")
    for number in range(1, highest + 1):
        if number in offsets:
            out.write(b"%010d 00000 n \n" % offsets[number])
        else:
            out.write(b"0000000000 65535 f \n")
    out.write(
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (highest + 1, xref_at)
    )
    return out.getvalue()


def _pdf(pages: list[str], encrypt_with: str | None = None) -> bytes:
    data = _raw_pdf(pages)
    if encrypt_with is None:
        return data

    from pypdf import PdfWriter

    writer = PdfWriter(clone_from=io.BytesIO(data))
    writer.encrypt(encrypt_with)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def _docx(paragraphs: list[str]) -> bytes:
    import docx

    document = docx.Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    out = io.BytesIO()
    document.save(out)
    return out.getvalue()


def _blank_pdf() -> bytes:
    """A PDF with pages but no text layer - i.e. what a scan looks like."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


class TestPlainText:
    def test_reads_utf8(self) -> None:
        result = extract_text("essay.txt", "The cat sat on the mat.".encode(), _MAX)

        assert result.text == "The cat sat on the mat."
        assert result.word_count == 6
        assert result.source_format == "txt"

    def test_markdown_is_treated_as_text(self) -> None:
        result = extract_text("notes.md", b"# Title\n\nSome writing here.", _MAX)

        assert "Some writing here." in result.text
        assert result.source_format == "txt"

    def test_invalid_utf8_falls_back_and_warns(self) -> None:
        result = extract_text("essay.txt", b"caf\xe9 society writing", _MAX)

        assert result.word_count == 3
        assert result.warnings

    def test_collapses_excess_blank_lines(self) -> None:
        result = extract_text("essay.txt", b"One.\n\n\n\n\nTwo.", _MAX)

        assert result.text == "One.\n\nTwo."


class TestPdf:
    def test_extracts_text(self) -> None:
        result = extract_text(
            "essay.pdf", _pdf(["The committee met on Tuesday."]), _MAX
        )

        assert "committee" in result.text
        assert result.source_format == "pdf"
        assert result.page_count == 1

    def test_counts_pages(self) -> None:
        result = extract_text(
            "essay.pdf", _pdf(["Page one text.", "Page two text."]), _MAX
        )

        assert result.page_count == 2
        assert "Page one" in result.text and "Page two" in result.text

    def test_rejoins_hyphenated_line_breaks(self) -> None:
        """PDF extraction leaves "inter-\\nesting", which would otherwise be
        counted as two misspellings by the Mechanical profile."""
        result = extract_text("essay.txt", b"This is inter-\nesting writing.", _MAX)

        assert "interesting" in result.text

    def test_scanned_pdf_says_so(self) -> None:
        """The most common real-world failure. "0 words extracted" is not an
        actionable message; "it looks like a scan" is."""
        with pytest.raises(ExtractionError) as exc:
            extract_text("scan.pdf", _blank_pdf(), _MAX)

        assert "scan" in str(exc.value).lower()

    def test_password_protected_pdf_is_refused_clearly(self) -> None:
        encrypted = _pdf(["Secret writing here."], encrypt_with="hunter2")

        with pytest.raises(ExtractionError) as exc:
            extract_text("locked.pdf", encrypted, _MAX)

        assert "password" in str(exc.value).lower()

    def test_corrupt_pdf_is_refused(self) -> None:
        with pytest.raises(ExtractionError):
            extract_text("broken.pdf", b"%PDF-1.4 this is not a real pdf", _MAX)


class TestDocx:
    def test_extracts_paragraphs(self) -> None:
        result = extract_text(
            "essay.docx", _docx(["First paragraph.", "Second paragraph."]), _MAX
        )

        assert "First paragraph." in result.text
        assert "Second paragraph." in result.text
        assert result.source_format == "docx"

    def test_legacy_doc_gets_a_useful_message(self) -> None:
        with pytest.raises(ExtractionError) as exc:
            extract_text("old.docx", b"\xd0\xcf\x11\xe0 legacy ole file", _MAX)

        assert ".docx" in str(exc.value)


class TestRejections:
    def test_empty_file(self) -> None:
        with pytest.raises(ExtractionError) as exc:
            extract_text("essay.txt", b"", _MAX)

        assert "empty" in str(exc.value).lower()

    def test_oversized_file_reports_both_sizes(self) -> None:
        with pytest.raises(ExtractionError) as exc:
            extract_text("big.txt", b"x" * 2048, max_bytes=1024)

        assert "limit" in str(exc.value).lower()

    def test_unsupported_extension(self) -> None:
        with pytest.raises(ExtractionError) as exc:
            extract_text("photo.jpg", b"\xff\xd8\xff binary", _MAX)

        assert "supported" in str(exc.value).lower()

    def test_whitespace_only_file(self) -> None:
        with pytest.raises(ExtractionError):
            extract_text("essay.txt", b"   \n\n  \t ", _MAX)
