# app/utils/embedder.py

import os
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient

model = SentenceTransformer("all-MiniLM-L6-v2")
client = PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="youtube_videos")

# def clean_old_embeddings(current_video_ids: list):
#     print("🧹 Cleaning old embeddings...")
#     all_docs = collection.get(include=["metadatas"])
#     ids_to_delete = []

#     for _id, meta in zip(all_docs["ids"], all_docs["metadatas"]):
#         if meta.get("video_id") not in current_video_ids:
#             ids_to_delete.append(_id)

#     if ids_to_delete:
#         collection.delete(ids=ids_to_delete)
#         print(f"✅ Deleted {len(ids_to_delete)} old embeddings.")
#     else:
#         print("✅ No outdated embeddings found.")

def embed_transcript(video_id: str, transcript_path: str):
    if not os.path.exists(transcript_path):
        print(f"[❌] Transcript not found for {video_id}")
        return

    # Clean embeddings
    current_ids = [
        f.replace(".txt", "") for f in os.listdir("documents") if f.endswith(".txt")
    ]

    # Skip if already embedded
    existing = collection.get(include=["metadatas"])  # ✅ only valid keys
    for _id, meta in zip(existing.get("ids", []), existing.get("metadatas", [])):

        if meta.get("video_id") == video_id:
            print(f"[⏭️] Embeddings already exist for {video_id}")
            return {"message": "Embeddings already exist."}


    # Load + chunk transcript
    with open(transcript_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
    ids = [f"{video_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"video_id": video_id}] * len(chunks)

    embeddings = model.encode(chunks).tolist()

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )
    return {"message": f"[✅] Stored {len(chunks)} chunks for {video_id}"}
