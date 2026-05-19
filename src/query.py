"""
query.py ~ the VinylSage question pipeline

Loads our initialized ChromaDB index that is built using build_index.py.
Accepts a user question, and retrieves related data chunks.
Finally, returns a cited Gemini answer.

Note: I run this directly from the root of the project

Author: Nicholas Kennedy
05/15/2026
"""


import os
from pathlib import Path

from add_album import process_add_album

import chromadb
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex
from llama_index.core.settings import Settings
from llama_index.core.schema import NodeWithScore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext




CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "VinylSage"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
TOP_K = 3


PROMPT_GROUND = """ You are VinylSage, an extremely experienced assistant for classic rock record collecting.
                Answer questions using ONLY the context provided below.
                If the context doesn't contain enough information to answer, say so honestly.
                Do not use outside knowledge - only this set of context.

                Context:
                    {context}

                Question:
                    {question}

                Answer:
                """




def load_index() -> VectorStoreIndex:
    """
        Retrieve the Index & Embedding Model set up in the build_index.py script
        Once loaded method returns the index
    """    
    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)

    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    try:
        collection = chroma_client.get_collection(COLLECTION_NAME)
    except Exception:
        raise RuntimeError(
                f"Collection '{COLLECTION_NAME}' not found. Try running build_index again"
        )
    
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context,
    )

    chunk_count = collection.count()
    
    print(f"Loaded index: {chunk_count} chunks from '{COLLECTION_NAME}'")
    
    return index
        




def input_query() -> str:
    """
        Get the input question from the user
    """
    query = input("Ask VinylSage:  ").strip()
    return query






def retrieve_chunks(index: VectorStoreIndex, query: str, top_k: int = TOP_K) -> list[NodeWithScore]:
    """
        retrieve data chunks from the built index
    """
    retriever = index.as_retriever(similarity_top_k=top_k)
    chunks = retriever.retrieve(query)

    return chunks
    

def build_prompt(query: str, chunks: list[NodeWithScore]) -> str:
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
    return PROMPT_GROUND.format(context=context, question=query)



def generate_answer(query: str, chunks: list[NodeWithScore]) -> str:
    """
        Call the llm to generate an answer to the retrieved query, using the xontext provided by the chunked data
    """
    llm = GoogleGenAI(model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))
    prompt = build_prompt(query, chunks)
    response = llm.complete(prompt)

    return str(response)





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

        print("\nSearching...")
        chunks = retrieve_chunks(index, query)

        if not chunks:
            print("No relevant chunks found")
            continue

        print("Generating answer...")
        answer = generate_answer(query, chunks)
        display_answer(answer, chunks)






if __name__ == "__main__":
     main()








