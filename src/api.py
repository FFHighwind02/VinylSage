"""
    api.py is the VinylSage backend file using FastAPI
    Restapi to enable usage of the query pipeline built with query.py and albums.py



    Endpoints:

        GET /health     - sanity check
        POST /query     - the main endpoint for a query
        GET /albums     - post a list of the albums supported in our index

"""

import os
import sys
from pathlib import Path



from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from llama_index.core.schema import NodeWithScore
from llama_index.llms.google_genai import GoogleGenAI
from pydantic import BaseModel




sys.path.insert(0, str(Path(__file__).parent))
from albums import ANCHOR_ALBUMS
from router import classify_query, extract_album_from_query
from vs_util import (
    TOP_K,
    format_discogs_answer,
    generate_answer_async,
    load_index,
    load_llm,
    retrieve_chunks,
)

load_dotenv()







# App setup
app = FastAPI(
    title="VinylSage API",
    description="The Classic Rock collector's knowledgeable companion",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)





# Requests/responses
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
    sources: list[SourceDisplay]
    route: str
    question: str





# Startup: load index and LLM once
index = None
llm: GoogleGenAI | None = None


@app.on_event("startup")
async def startup():
    global index, llm
    print("Loading embedding model...")
    index = load_index()  # handles embedding config + ChromaDB connection
    print("Loading LLM...")
    llm = load_llm()
    print("\nVINYLSAGE API is Ready!")




@app.get("/health")
async def health():
    return {"status": "ok", "service": "VinylSage API"}





@app.get("/albums")
async def list_albums():
    return {
        "count": len(ANCHOR_ALBUMS),
        "albums": [
            {"title": a["title"], "artist": a["artist"]}
            for a in ANCHOR_ALBUMS
        ],
    }




@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if index is None or llm is None:
        raise HTTPException(status_code=503, detail="Index not loaded yet")

    # Route the query
    route = await classify_query(request.question)

    if route == "discogs":
        album = extract_album_from_query(request.question, ANCHOR_ALBUMS)
        if album:
            answer = format_discogs_answer(album["artist"], album["title"])
            return QueryResponse(
                answer=answer,
                sources=[],
                route="discogs",
                question=request.question,
            )
        # Album not identified — fall through to RAG
        route = "rag"

    # RAG path
    chunks = retrieve_chunks(request.question, index, request.top_k)
    if not chunks:
        return QueryResponse(
            answer="No relevant information found. Try rephrasing your question.",
            sources=[],
            route="rag",
            question=request.question,
        )

    answer = await generate_answer_async(request.question, chunks, llm)
    sources = [
        SourceDisplay(
            album=c.metadata.get("album", "Unknown"),
            artist=c.metadata.get("artist", "Unknown"),
            url=c.metadata.get("url", ""),
            relevance=round(c.score or 0.0, 3),
        )
        for c in chunks
    ]

    return QueryResponse(
        answer=answer,
        sources=sources,
        route="rag",
        question=request.question,
    )
