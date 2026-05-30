"""
    api.py is the VinylSage backend file using FastAPI

    Endpoints:

        GET
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








load_dotenv()



CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
DISCOGS_DIR = Path(__file__).parent.parent / "data" / "raw" / "discogs"
COLLECTION_NAME = "VinylSage"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
TOP_K = 5




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




        











