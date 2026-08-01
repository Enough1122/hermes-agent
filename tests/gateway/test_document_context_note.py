"""Tests for the document context note prepended to user turns with attachments.

A user who attaches a PDF / DOCX in chat used to see the agent treat it as
"unreadable" because the context note told the model to "Ask the user what
they'd like you to do with it" — steering it away from extracting the text it
is perfectly capable of reading. These tests pin the contract:

- text documents: when content is inlined the note confirms that + records the
  path; when inlining was skipped it must NOT promise "included below" (#76022).
- binary documents (PDF/DOCX/…): note tells the agent to extract the text
  itself and never tells it to punt back to the user.
"""

import importlib

import pytest

gateway_run = importlib.import_module("gateway.run")
_build_document_context_note = gateway_run._build_document_context_note
_read_text_document_for_inline = gateway_run._read_text_document_for_inline


class TestTextDocumentNote:
    @pytest.mark.parametrize("mtype", ["text/plain", "text/markdown", "text/csv"])
    def test_text_note_with_inlined_content_promises_it(self, mtype):
        note = _build_document_context_note(
            "notes.txt", "/cache/doc_notes.txt", mtype, content_inlined=True
        )
        assert "text document" in note
        assert "notes.txt" in note
        assert "/cache/doc_notes.txt" in note
        assert "included below" in note

    @pytest.mark.parametrize("mtype", ["text/plain", "text/markdown", "text/csv"])
    def test_text_note_without_inlined_content_does_not_promise_it(self, mtype):
        """#76022: when content could not be inlined the note must not claim
        "included below" — otherwise the model confidently answers from a file
        it has never seen. It must point at the path instead."""
        note = _build_document_context_note(
            "notes.txt", "/cache/doc_notes.txt", mtype, content_inlined=False
        )
        assert "notes.txt" in note
        assert "/cache/doc_notes.txt" in note
        assert "included below" not in note
        # And it must not punt the user back into pasting contents.
        assert "ask the user" not in note.lower()
        assert "paste" in note.lower()

    def test_default_content_inlined_is_false(self):
        """The default keeps the old call sites honest: without explicitly
        opting in, no "included below" promise is made."""
        note = _build_document_context_note("a.txt", "/cache/a.txt", "text/plain")
        assert "included below" not in note


class TestBinaryDocumentNote:
    @pytest.mark.parametrize(
        "mtype",
        [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/octet-stream",
        ],
    )
    def test_binary_note_guides_extraction(self, mtype):
        note = _build_document_context_note("contract.pdf", "/cache/doc_contract.pdf", mtype)
        # Records the path so the agent can open it.
        assert "/cache/doc_contract.pdf" in note
        # Tells the agent to read it by extracting the text...
        assert "extract" in note.lower()
        # ...and does NOT steer it into punting back to the user (the bug).
        assert "ask the user" not in note.lower()
        assert "paste" in note.lower()


class TestReadTextDocumentForInline:
    """#76022: the helper that reads a text document for inline inclusion."""

    def test_reads_small_file(self, tmp_path):
        p = tmp_path / "notes.txt"
        p.write_text("hello world\n", encoding="utf-8")
        assert _read_text_document_for_inline(str(p)) == "hello world\n"

    def test_missing_file_returns_none(self, tmp_path):
        assert _read_text_document_for_inline(str(tmp_path / "nope.txt")) is None

    def test_empty_file_returns_none(self, tmp_path):
        p = tmp_path / "empty.txt"
        p.write_bytes(b"")
        assert _read_text_document_for_inline(str(p)) is None

    def test_truncation_marker_added(self, tmp_path):
        cap = gateway_run._INLINE_TEXT_MAX_BYTES
        p = tmp_path / "big.txt"
        payload = b"x" * (cap + 4096)
        p.write_bytes(payload)
        out = _read_text_document_for_inline(str(p))
        assert out is not None
        # Capped body present ...
        assert out.startswith("x" * cap)
        # ... plus a visible truncation marker pointing at the full file.
        assert "truncated" in out.lower()
        assert str(p) in out

    def test_invalid_utf8_does_not_raise(self, tmp_path):
        p = tmp_path / "binish.txt"
        p.write_bytes(b"caf\xff\xfe hello")
        out = _read_text_document_for_inline(str(p))
        assert out is not None
        assert "hello" in out

    def test_exactly_at_cap_not_truncated(self, tmp_path):
        cap = gateway_run._INLINE_TEXT_MAX_BYTES
        p = tmp_path / "exact.txt"
        p.write_bytes(b"a" * cap)
        out = _read_text_document_for_inline(str(p))
        assert out is not None
        assert "truncated" not in out.lower()
        assert len(out) == cap
