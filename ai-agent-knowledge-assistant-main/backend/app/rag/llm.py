from collections.abc import Iterator
from functools import lru_cache

from openai import OpenAI

from app.config import get_settings

settings = get_settings()


@lru_cache
def _client() -> OpenAI:
    kwargs = {"api_key": settings.openai_api_key or "not-set"}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**kwargs)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    client = _client()
    resp = client.embeddings.create(model=settings.embedding_model, input=texts)
    return [d.embedding for d in resp.data]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]


SYSTEM_PROMPT = (
    "You are a helpful knowledge assistant. Answer the user's question primarily "
    "using the provided context. Cite sources inline using the [#] markers next to "
    "each context block. If the context is only partially relevant, use what is "
    "there and say what is missing. Only say you don't have enough information when "
    "the context is truly unrelated to the question. Be concise."
)


def _messages(question: str, context_blocks: list[str]) -> list[dict]:
    context = "\n\n".join(context_blocks) if context_blocks else "(no context found)"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]


def generate_answer(question: str, context_blocks: list[str]) -> str:
    resp = _client().chat.completions.create(
        model=settings.chat_model,
        messages=_messages(question, context_blocks),
        temperature=0.2,
        max_tokens=settings.max_tokens,
    )
    return resp.choices[0].message.content or ""


def stream_answer(question: str, context_blocks: list[str]) -> Iterator[str]:
    """Yield answer tokens as they are generated for low perceived latency."""
    stream = _client().chat.completions.create(
        model=settings.chat_model,
        messages=_messages(question, context_blocks),
        temperature=0.2,
        max_tokens=settings.max_tokens,
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
