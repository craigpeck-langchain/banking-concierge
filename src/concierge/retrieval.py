"""Vector-store retrieval over the synthetic banking knowledge base."""

from __future__ import annotations

import os
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

KB_DIR = Path(__file__).parent / "kb"


def _make_embeddings() -> OpenAIEmbeddings:
    # Embeddings must go directly to OpenAI. The LangSmith gateway only
    # allow-lists chat completions, not /embeddings, so when BASE_URL /
    # OPENAI_BASE_URL point at the gateway (as they do for the chat model in
    # graph.py) a default embeddings client inherits OPENAI_BASE_URL and gets a
    # 403/501 from the gateway. Pin the embeddings endpoint to OpenAI directly.
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        base_url="https://api.openai.com/v1",
        api_key=os.environ["OPENAI_API_KEY"],
    )


def _load_kb_documents() -> list[Document]:
    docs: list[Document] = []
    for md_path in sorted(KB_DIR.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        docs.append(
            Document(
                page_content=text,
                metadata={"source": md_path.name, "topic": md_path.stem},
            )
        )
    return docs


_VECTOR_STORE: InMemoryVectorStore | None = None


def get_vector_store() -> InMemoryVectorStore:
    """Return the KB vector store, memoizing only on successful construction."""
    # Only cache on success — if construction raises (e.g. missing
    # OPENAI_API_KEY at process start), leave the cache unset so the next
    # call retries instead of pinning a transient credential outage for
    # the pod lifetime.
    global _VECTOR_STORE
    if _VECTOR_STORE is not None:
        return _VECTOR_STORE
    docs = _load_kb_documents()
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    chunks = splitter.split_documents(docs)
    embeddings = _make_embeddings()
    _VECTOR_STORE = InMemoryVectorStore.from_documents(chunks, embeddings)
    return _VECTOR_STORE


def retrieve(query: str, k: int = 4) -> list[Document]:
    return get_vector_store().similarity_search(query, k=k)
