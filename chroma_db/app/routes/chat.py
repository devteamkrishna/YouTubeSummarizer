import os
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.utils.embedder import embed_transcript

load_dotenv()
router = APIRouter()
API_KEY = os.getenv("API_KEY")

# 🔐 Groq client
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

# 🧠 Embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# 🗂️ Chroma setup
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("youtube_videos")

# 📥 Request model
class ChatRequest(BaseModel):
    video_id: str
    query: str

# 🔍 Retrieve relevant chunks
def retrieve_context(video_id: str, query: str, k: int = 5) -> list[str]:
    query_embedding = embedding_model.encode([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        where={"video_id": video_id}
    )
    return results["documents"][0] if results["documents"] else []

# 💬 Chat with context using Groq
def chat_with_rag_context(video_id: str, query: str) -> str:
    context_chunks = retrieve_context(video_id, query)
    context_text = "\n\n".join(context_chunks)

    prompt = f"""Answer the question using the following video transcript context. If the context is not sufficient, just say you don't have the answer.

    ### Context:
    {context_text}

    ### Question:
    {query}

    ### Answer:"""

    response = groq_client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )

    return response.choices[0].message.content.strip()

# 🚀 FastAPI route
# @router.post("/chat_with_video")
# def chat_with_video(data: ChatRequest, request: Request):
#     if request.headers.get("x-api-key") != API_KEY:
#         raise HTTPException(status_code=403, detail="Invalid API Key")
#     try:
#         answer = chat_with_rag_context(data.video_id, data.query)
#         return {"answer": answer}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat_video")
def chat_with_video(data: ChatRequest, request: Request):
    if request.headers.get("x-api-key") != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    video_id = data.video_id
    transcript_path = os.path.join("documents", f"{video_id}.txt")

    if not os.path.exists(transcript_path):
        raise HTTPException(status_code=404, detail="Transcript file not found.")

    # 🧠 Check if already embedded
    existing = collection.get(where={"video_id": video_id})
    if not existing["ids"]:
        try:
            print(f"🔁 Embedding on-demand for video: {video_id}")
            result = embed_transcript(video_id, transcript_path)
            if result:
                print(result.get("message"))
        except Exception as e:
            print(f"[❌] Embedding failed for {video_id}: {e}")
            raise HTTPException(status_code=500, detail="Embedding failed")

    # ✅ Continue to answer chat
    try:
        answer = chat_with_rag_context(video_id, data.query)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
