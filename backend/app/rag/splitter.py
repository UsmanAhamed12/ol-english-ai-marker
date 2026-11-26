"""Cutting a document into chunks the retriever can rank.

A chunk is the unit of retrieval: too big and one paragraph about the present
perfect is buried in three pages of syllabus, too small and it loses the sentence
that gives it meaning. 1100 characters is about two paragraphs of a past paper.
"""

import re

CHUNK_CHARS = 1100

# Words that carry no meaning for retrieval. Keeping them out of the index is what
# makes the lexical fallback useful instead of noise.
STOP = {
    "the", "and", "that", "this", "with", "from", "have", "they", "will", "your", "their",
    "which", "what", "when", "were", "been", "than", "then", "into", "also", "must", "should",
    "answer", "question", "marks", "paper", "test", "award", "awarded", "candidate",
}


def terms(text: str) -> list[str]:
    """The words a query and a chunk can be compared on."""
    return [w for w in re.findall(r"[a-z][a-z'-]{3,}", (text or "").lower()) if w not in STOP]


def chunk_text(content: str) -> list[str]:
    """Pack paragraphs into ~1100-character chunks, splitting overlong paragraphs."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content or "") if p.strip()]
    chunks: list[str] = []
    buffer = ""

    for paragraph in paragraphs:
        pieces = (
            [paragraph]
            if len(paragraph) <= CHUNK_CHARS
            else [paragraph[i : i + CHUNK_CHARS] for i in range(0, len(paragraph), CHUNK_CHARS)]
        )
        for piece in pieces:
            if buffer and len(buffer) + len(piece) > CHUNK_CHARS:
                chunks.append(buffer)
                buffer = piece
            else:
                buffer = f"{buffer}\n{piece}" if buffer else piece
    if buffer:
        chunks.append(buffer)
    return chunks