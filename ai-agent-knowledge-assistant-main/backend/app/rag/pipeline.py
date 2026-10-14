from collections.abc import Iterator

from app.config import get_settings
from app.rag import llm, vectorstore
from app.rag.chunking import chunk_text, extract_text

settings = get_settings()


def _retrieve(question: str, top_k: int | None) -> tuple[list[str], list[dict]]:
    k = top_k or settings.top_k
    query_emb = llm.embed_query(question)
    hits = vectorstore.query(query_emb, k)

    context_blocks: list[str] = []
    sources: list[dict] = []
    for i, hit in enumerate(hits, start=1):
        context_blocks.append(f"[{i}] (from {hit['filename']})\n{hit['text']}")
        sources.append(
            {
                "document_id": hit["document_id"],
                "filename": hit["filename"],
                "chunk_index": hit["chunk_index"],
                "snippet": hit["text"][:280],
                "score": hit["score"],
            }
        )
    return context_blocks, sources


def ingest_document(
    document_id: str, filename: str, content_type: str, raw: bytes
) -> tuple[int, int]:
    """Extract, chunk, embed and store a document. Returns (num_chunks, num_chars)."""
    text = extract_text(filename, content_type, raw)
    if not text:
        return 0, 0

    chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        return 0, len(text)

    embeddings = llm.embed_texts(chunks)
    vectorstore.add_chunks(document_id, filename, chunks, embeddings)
    return len(chunks), len(text)


def answer_question(question: str, top_k: int | None = None) -> dict:
    context_blocks, sources = _retrieve(question, top_k)
    answer = llm.generate_answer(question, context_blocks)
    return {"answer": answer, "sources": sources}


def retrieve_sources(question: str, top_k: int | None = None) -> tuple[list[str], list[dict]]:
    """Retrieve context blocks + source metadata without generating an answer."""
    return _retrieve(question, top_k)


def stream_answer(question: str, context_blocks: list[str]) -> Iterator[str]:
    yield from llm.stream_answer(question, context_blocks)
