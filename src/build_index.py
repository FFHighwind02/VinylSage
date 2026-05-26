"""
build_index.py ~ pipelines the raw data retrieved from the pull scripts and API sources (Wikipedia, Discogs) and
subsequently stores the data in usable chunks that will not eat up LLMs token limits


RAW DATA -> DOCUMENT FORM -> CHUNKS -> EMBED -> STORE


05/23/26
Author: Nicholas Kennedy
"""



import json
from pathlib import Path


import chromadb

# Llama index accesses for building chroma DB
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore



RAW_DIR = Path(__file__).parent.parent / "data" / "raw" / "wikipedia"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

COLLECTION_NAME = "VinylSage"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50






def load_documents() -> list[Document]:
    """
    Transform the raw JSON data retrieved in the pull script into list of Documents.
    
    """
    json_files = sorted(RAW_DIR.glob("*.json"))
    print(f"Found {len(json_files)} JSON files to process")

    documents = []

    for filepath in json_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)


        # Extra context as model was pulling unrelated chunks into test questions
        pretext = (
                f"Album: {data['title']}\n"
                f"Artist: {data['artist']}\n"
                f"Source: Wikipedia\n\n"
        )



        doc = Document(                 # document struct 
            text=data["full_text"],
            metadata={
                "album": data["title"],
                "artist": data["artist"],
                "wiki_title": data["wiki_title"],
                "url": data["url"],
                "source": data["source"],
            },
            metadata_seperator="\n",
            metadata_form="{key}: {value}",
            text_form="Metadata:\n{metadata_str}\n\nContent:\n{content}",

        )
        

        documents.append(doc)
        print(f" Loaded: {data['artist']} - {data['title']} ({len(data['full_text'])} chars loaded...)")
    

    return documents






def build_index(documents: list[Document]) -> VectorStoreIndex:
    
    """Chunk documents, embed them, and store in ChromaDB."""


    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)
    Settings.node_parser = SentenceSplitter(
        chunk_size=CHUNK_SIZE,          # for ref: chunk_size = 512 tokens
        chunk_overlap=CHUNK_OVERLAP,    
    )


    # ChromaDB setup
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Wipe leftover collection
    try:
        chroma_client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection: {COLLECTION_NAME}")
    except Exception:
        pass


    collection = chroma_client.create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print(f"\nBuilding index (chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    print("\nDownloading the embedding model (~80MB)...\n")

    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True,
    )

    return index






def main():


    print("/*" * 30)
    print("Welcome to VinylSage's build index")
    print("/*" * 30)

    documents = load_documents()

    if not documents:
        print("\nError: no documents found, run the pull_wikipedia.py to collect some")
        return

    print(f"Loading {len(documents)} docs...")

    index = build_index(documents)



    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_collection(COLLECTION_NAME)
    chunk_count = collection.count()


    print("\n\n")
    print("/*" * 30)
    print(f"Done. Indexed {chunk_count} chunks from {len(documents)} albums.")
    print(f"Storage: {CHROMA_DIR}")
    print("=" * 60)






if __name__ == "__main__":
    main()





