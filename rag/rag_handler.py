# rag/rag_handler.py

import os
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from fastapi import HTTPException

CHUNK_SIZE = 300
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

def chunk_text(text, chunk_size=CHUNK_SIZE):
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]


def embed_and_store_chunks(video_id: str, file_path: str):
    # ❓ Check if transcript exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Transcript file not found")

    # 🧠 Read transcript
    with open(file_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    # 📚 Chunking
    chunks = chunk_text(transcript)
    ids = [f"{video_id}_{i}" for i in range(len(chunks))]

    # 🤖 Load model & embed
    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = model.encode(chunks).tolist()

    # 🧠 ChromaDB setup
    # client = chromadb.Client()
    client = chromadb.Client(Settings(persist_directory="chroma_db"))
    collection = client.get_or_create_collection(name=video_id)

    # 🧪 Check for existing IDs (avoid reprocessing)
    existing = collection.get(ids=[ids[0]])  # only need to check first
    if existing["ids"]:
        print(f"⚠️ Embeddings already exist for video: {video_id}")
        return {"message": "Embeddings already exist."}

    # 💾 Store
    collection.add(documents=chunks, embeddings=embeddings, ids=ids)
    if hasattr(client, "persist"):
        client.persist()
    print(f"✅ Stored {len(chunks)} chunks for video {video_id}")

    return {"message": f"Embedded and stored {len(chunks)} chunks."}


# def embed_and_store_chunks(video_id: str, file_path: str):
#     # Check if vector store already has embeddings for this video
#     existing_ids = collection.get(ids=[video_id])  # or a prefix match
#     if existing_ids["ids"]:
#         print(f"⚠️ Embeddings already exist for video: {video_id}")
#         return  # Skip processing
    
#     if not os.path.exists(file_path):
#         raise HTTPException(status_code=404, detail="Transcript file not found")

#     with open(file_path, "r", encoding="utf-8") as f:
#         transcript = f.read()

#     chunks = chunk_text(transcript)
#     ids = [f"{video_id}_{i}" for i in range(len(chunks))]

#     model = SentenceTransformer(EMBEDDING_MODEL)
#     embeddings = model.encode(chunks).tolist()

#     client = chromadb.Client()
#     collection = client.get_or_create_collection(name=video_id)
#     collection.add(documents=chunks, embeddings=embeddings, ids=ids)

#     return {"message": f"Embedded and stored {len(chunks)} chunks."}

def setup_rag_session(video_id: str):
    client = chromadb.Client()
    collection = client.get_or_create_collection(name=video_id)
    return collection
