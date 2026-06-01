"""
query.py ~ the VinylSage question pipeline

Loads our initialized ChromaDB index that is built using build_index.py.
Accepts a user question, and retrieves related data chunks.
Finally, returns a cited Gemini answer.

Note: I run this directly from the root of the project

Author: Nicholas Kennedy
05/15/2026
"""

import sys
import asyncio


from pathlib import Path
from dotenv import load_dotenv
from llama_index.core.schema import NodeWithScore

from add_album import process_add_album
from router import classify_query_sync, extract_album_from_query
from albums import ANCHOR_ALBUMS


sys.path.insert(0, str(Path(__file__).parent))
from albums import ANCHOR_ALBUMS
from router import classify_query, extract_album_from_query
from vs_util import (
    TOP_K,
    format_discogs_answer,
    generate_answer,
    load_index,
    load_llm,
    retrieve_chunks,
)

CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
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





def input_query() -> str:
    """
        Get the input question from the user
    """
    query = input("Ask VinylSage:  ").strip()
    return query





def display_answer(answer: str, chunks: list[NodeWithScore]) -> None:
    """
        Provide text output to inform and direct users regarding the run of the current command line
        version of the app
    """
    print("\n" + "/*" * 30)
    print("ANSWER:")
    print("/*" * 30)
    print(answer)

    
    print("\n" + "-" * 30)
    print("SOURCES")
    print("-" * 30)

    
    for i, chunk in enumerate(chunks, 1):

        album = chunk.metadata.get("album", "Unknown")
        artist = chunk.metadata.get("artist", "Unknown")
        url = chunk.metadata.get("url", "")
        score = chunk.score if chunk.score is not None else 0.0

        print(f"  [{i}] {artist} - {album}")
        print(f"       Relevance: {score:.3f}")
        
        if url:
            print("\t" * 2 + url)
    
    print("-" * 30)
    
    





def main():

    load_dotenv()

    print("=" * 30)
    print("VinylSage — The Classic Rock Collector's Best Friend")
    print("=" * 30)
    print("Loading index...")

    index = load_index()
    llm = load_llm()

    print(f"Debug: {type(index)}")

    # Keep asking until the user chooses to exit
    print("\nType your question or 'quit' to exit.")
    
    while True:

        query = input_query()

        if not query:
            print("Please enter a question.")
            continue

        if query.lower() in ("quit", "exit", "q"):
            print("Thanks for chatting. See you next time!")
            break

        
        route = classify_query_sync(query)

        print(f"\n[Route: {route.upper()}] Searching...")

        if route == "discogs":
            # Try to identify which album they're asking about
            album = extract_album_from_query(query, ANCHOR_ALBUMS)
            if album:
                answer = format_discogs_answer(album["artist"], album["title"])
                print("\n" + "=" * 60)
                print("PRESSING DATA")
                print("=" * 60)
                print(answer)
                print("=" * 60)
                continue
        

        chunks = retrieve_chunks(query, index)
        if not chunks:
            print("No relevant chunks found..")
            continue

        answer = generate_answer(query, chunks)
        display_answer(answer, chunks)


if __name__ == "__main__":
     main()








