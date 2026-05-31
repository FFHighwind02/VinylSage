"""
    api.py is the VinylSage backend file using FastAPI
    Restapi to enable usage of the query pipeline built with query.py and albums.py



    Endpoints:

        GET /system     - sanity check
        POST /query     - the main endpoint for a query
        GET /albums     - post a list of the albums supported in our index

"""


import json
import os 
import sys



from pathlib import Path

import chromadb
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import BaseModel



sys.path.insert(0,str(Path(__file__).parent))
from albums import ANCHOR_ALBUMS
from router import classify_query, extract_album_from_query



load_dotenv()


# Copied config from query.puy
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
DISCOGS_DIR = Path(__file__).parent.parent / "data" / "raw" / "discogs"
COLLECTION_NAME = "VinylSage"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
TOP_K = 5


PROMPT_GROUND = """ You are VinylSage, an extremely experienced assistant for classic rock record collecting.
                Answer questions using ONLY the context provided below.
                If the context doesn't contain enough information to answer, say so honestly, but use what is there and state what information is missing.
                Do not use outside knowledge - only this set of context.

                Context:
                    {context}

                Question:
                    {question}

                Answer (be specific and cite details from the context):
                """


app = FastAPI(
        title="VinylSage API",
        description="The Classic Rock collector's knowledgable companion",
        version="0.1.0",
)


app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
)




# The requests and responses interacted w/ user
class QueryRequest(BaseModel):
    question: str
    top_k: int = TOP_K



class SourceDisplay(BaseModel):
    album: str
    artist: str
    url: str
    relevance: float




class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    route: str
    question: str




# Startup proc
index: VectorStoreIndex | None = None
llm: GoogleGenAI | None = None


@app.on_event("startup")
async def startup():
    
    global index, llm

    print("Loading embedding...")
    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)


    print("Connecting to chromadb...")
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        collection = chroma_client.get_collection(COLLECTION_NAME)
    except Exception:
        raise RuntimeError(f"Collection: {COLLECTION_NAME} cannot be found, run build_index.")


    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)

    llm = GoogleGenAI(
            model="gemini-2.5-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
        )

    print("\nVINYLSAGE API is Ready!")





def slugify(text: str) -> str:
    return (
        text.lower()
        .replace(" ", "-")
        .replace("'", "")
        .replace(".", "")
        .replace("/", "-")
        .replace(":", "")
    )


















