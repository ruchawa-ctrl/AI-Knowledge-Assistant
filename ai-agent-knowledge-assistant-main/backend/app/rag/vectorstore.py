import chromadb

from app.config import get_settings

settings = get_settings()

_client = chromadb.PersistentClient(path=settings.chroma_path)
_collection = _client.get_or_create_collection(
    name="documents", metadata={"hnsw:space": "cosine"}
)


def add_chunks(
    document_id: str,
    filename: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    ids = [f"{document_id}:{i}" for i in range(len(chunks))]
    metadatas = [
        {"document_id": document_id, "filename": filename, "chunk_index": i}
        for i in range(len(chunks))
    ]
    _collection.add(
        ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas
    )


def query(embedding: list[float], top_k: int) -> list[dict]:
    res = _collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]

    results = []
    for doc, meta, dist in zip(docs, metas, dists):
        results.append(
            {
                "text": doc,
                "document_id": meta.get("document_id", ""),
                "filename": meta.get("filename", ""),
                "chunk_index": int(meta.get("chunk_index", 0)),
                # cosine distance -> similarity score
                "score": round(1.0 - float(dist), 4),
            }
        )
    return results


def delete_document(document_id: str) -> None:
    _collection.delete(where={"document_id": document_id})
