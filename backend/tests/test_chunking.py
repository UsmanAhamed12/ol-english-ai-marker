"""Chunking and the lexical scorer: the retrieval fallback must be dependable."""

from app.rag.splitter import chunk_text, terms


def test_short_text_is_one_chunk():
    assert chunk_text("Test 1: (1) c (2) e") == ["Test 1: (1) c (2) e"]


def test_paragraphs_are_packed_then_split_on_the_limit():
    paragraphs = ["a" * 700, "b" * 700, "c" * 700]
    chunks = chunk_text("\n\n".join(paragraphs))
    # Two 700-character paragraphs exceed the 1100 limit, so each stands alone.
    assert len(chunks) == 3
    assert all(len(chunk) <= 1100 for chunk in chunks)


def test_small_paragraphs_share_one_chunk():
    assert chunk_text("first line\n\nsecond line") == ["first line\nsecond line"]


def test_an_overlong_paragraph_is_split_without_losing_characters():
    text = "x" * 2500
    chunks = chunk_text(text)
    assert len(chunks) == 3
    assert sum(len(chunk) for chunk in chunks) == 2500


def test_empty_content_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_terms_drop_stop_words_and_short_tokens():
    found = terms("The candidate must answer the question about a train delay")
    assert "train" in found
    assert "delay" in found
    assert "the" not in found
    assert "answer" not in found


def test_terms_are_lowercased():
    assert terms("PLATFORM") == ["platform"]