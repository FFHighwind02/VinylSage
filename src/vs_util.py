"""
utils.py — Shared utility and helpers for VinylSage


Refactored to avoid duplication
Imported by both query.py and api.py.
"""

import json
import os
from pathlib import Path



import chromadb
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.vector_stores.chroma import ChromaVectorStore


# Setup constants /**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/*
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
DISCOGS_DIR = Path(__file__).parent.parent / "data" / "raw" / "discogs"
COLLECTION_NAME = "VinylSage"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
TOP_K = 5


PROMPT_TEMPLATE = """ You are VinylSage, an extremely experienced assistant for classic rock record collecting.
                Answer questions using ONLY the context provided below.
                If the context doesn't contain enough information to answer, say so honestly, but use what is there and state what information is missing.
                Do not use outside knowledge - only this set of context.

                Context:
                    {context}

                Question:
                    {question}

                Answer (be specific and cite details from the context):
                """




# Utility functions /*/**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/**/*



def slugify(text: str) -> str:
    """Convert string to safe filename component."""
    return (
        text.lower()
        .replace(" ", "-")
        .replace("'", "")
        .replace(".", "")
        .replace("/", "-")
        .replace(":", "")
    )





def load_index() -> VectorStoreIndex:
    """
        Retrieve the Index & Embedding Model set up in the build_index.py script
        Once loaded, method returns the index
    """
    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)

    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    try:
        collection = chroma_client.get_collection(COLLECTION_NAME)
    except Exception:
        raise RuntimeError(f"Collection '{COLLECTION_NAME}' not found. Try running build_index again")


    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context,
    )

    chunk_count = collection.count()

    print(f"Loaded index: {chunk_count} chunks from '{COLLECTION_NAME}'")
    
    return index







def load_llm() -> GoogleGenAI:
    """Instantiate the Gemini LLM."""
    return GoogleGenAI(
        model="gemini-2.5-flash",
        api_key=os.getenv("GOOGLE_API_KEY"),
    )





def retrieve_chunks(question: str, index: VectorStoreIndex, top_k: int = TOP_K) -> list[NodeWithScore]:
    """Embed question and retrieve top-K similar chunks from the built index."""

    retriever = index.as_retriever(similarity_top_k=top_k)
    chunks = retriever.retrieve(question)
    
    return chunks







def build_prompt(question: str, chunks: list[NodeWithScore]) -> str:
    """
    Combine retrieved chunks into a grounded prompt for Gemini.
    Each chunk is labelled with its source for clarity.
    """
    context_parts = []

    for i, chunk in enumerate(chunks, 1):
        album = chunk.metadata.get("album", "Unknown Album")
        artist = chunk.metadata.get("artist", "Unknown Artist")
        context_parts.append(
            f"[Source {i}: {artist} - {album}]\n{chunk.text}"
        )

    context = "\n\n".join(context_parts)
    return PROMPT_TEMPLATE.format(context=context, question=question)






def generate_answer(question: str, chunks: list[NodeWithScore]) -> str:
    """
        Send grounded prompt to Gemini, return answer string.
    """
    llm = GoogleGenAI(model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))
    prompt = build_prompt(question, chunks)
    response = llm.complete(prompt)
    
    return str(response)





async def generate_answer_async(question: str, chunks: list, llm) -> str:
    """Async version — used by API (api.py)."""
    prompt = build_prompt(question, chunks)
    response = await llm.acomplete(prompt)
    return str(response)




def load_discogs_data(artist: str, title: str) -> dict | None:
    """
    Load saved Discogs JSON for an album. Returns None if not found.
    """

    filename = f"{slugify(artist)}_{slugify(title)}.json"
    filepath = DISCOGS_DIR / filename
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)






def format_discogs_answer(artist: str, title: str) -> str:
    """
        Format Discogs pressing data as a readable string.
    """
    data = load_discogs_data(artist, title)
    if not data:
        return f"No Discogs data found for {artist} - {title}. Try re-running pull_discogs.py."

    pressings = data.get("pressings", [])
    master = data.get("master", {})
    countries = data.get("countries", [])
    years = data.get("years_range", {})

    lines = [
        f"{artist} — {title}",
        f"Original release: {master.get('year', 'Unknown')}",
        f"Total known pressings: {len(pressings)}",
        f"Countries: {', '.join(countries) if countries else 'Unknown'}",
        f"Years range: {years.get('earliest', '?')} – {years.get('latest', '?')}",
        "",
        "Notable pressings (earliest first):",
    ]

    for p in pressings[:10]:
        country = p.get("country", "Unknown")
        year = p.get("year", "?")
        label = p.get("label", "Unknown")
        catno = p.get("catalog_number", "")
        fmt = p.get("format", "")
        lines.append(f"  • {year} | {country} | {label} | {catno} | {fmt}")

    return "\n".join(lines)







