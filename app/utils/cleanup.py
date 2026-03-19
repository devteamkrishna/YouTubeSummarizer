# app/utils/cleanup.py
import os
import shutil
from chromadb import PersistentClient

DOCUMENTS_DIR = "documents"

def clear_chroma_embeddings(db_path="./chroma_db", collection_name="youtube_videos"):
    client = PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name=collection_name)
    all_docs = collection.get(include=[])
    all_ids = all_docs.get("ids", [])

    if all_ids:
        collection.delete(ids=all_ids)
        print(f"✅ Deleted {len(all_ids)} embeddings.")
    else:
        print("✅ No embeddings to delete.")

def clear_old_transcripts():
    if os.path.exists(DOCUMENTS_DIR):
        shutil.rmtree(DOCUMENTS_DIR)
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    print("🧹 Old transcriptions folder cleared.")
