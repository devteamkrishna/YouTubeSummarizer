import os
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.utils.embedder import embed_transcript
from webvtt import WebVTT
from yt_dlp import YoutubeDL



load_dotenv()
router = APIRouter()
API_KEY = os.getenv("API_KEY")

# 🔐 Groq client
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

# 🧠 Embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

DOCUMENTS_DIR = "documents"

# 🗂️ Chroma setup
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("youtube_videos")

# 📥 Request model
class ChatRequest(BaseModel):
    video_id: str
    query: str

# 📄 Convert VTT to TXT
def convert_vtt_to_txt(vtt_path: str, txt_path: str, metadata: dict = None):
    try:
        vtt = WebVTT().read(vtt_path)
        seen = set()
        lines = []

        for caption in vtt:
            for line in caption.text.strip().splitlines():
                clean_line = line.strip()
                if clean_line and clean_line not in seen:
                    lines.append(clean_line)
                    seen.add(clean_line)

        cleaned_text = "\n".join(lines)

        meta_block = ""
        if metadata:
            meta_lines = [f"{k}: {v}" for k, v in metadata.items()]
            meta_block = "Here is the YouTuber's channel information and metadata, included for reference:\n" + "\n".join(meta_lines) + "\n\n"

        full_text = meta_block + cleaned_text

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        print(f"[✅] Transcript saved to: {txt_path}")

    except Exception as e:
        print(f"[❌] Failed to convert VTT to TXT: {e}")


# 📥 Download and transcribe video
def download_and_transcribe(video_id: str, video_url: str, metadata: dict = None) -> str:
    """Download VTT subtitles using yt_dlp and convert to TXT."""
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "best",
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en", "en-US", "en-GB", "en-CA", "en-AU", "en-IN", "en-IE", "en-NZ", "en-ZA", "en-PH", "en-SG"],
        "outtmpl": f"{DOCUMENTS_DIR}/%(id)s.%(ext)s",
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # ydl.download([video_url])
            info = ydl.extract_info(video_url, download=True)  # One efficient call

            metadata = {
                "Creator": info.get("uploader", "Unknown"),
                "Channel ID": info.get("uploader_id", "N/A"),
                "Channel URL": info.get("uploader_url", "N/A"),
                "Subscribers": info.get("channel_follower_count", "N/A"),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subtitle download failed: {e}")

    vtt_path = None
    for file in os.listdir(DOCUMENTS_DIR):
        if file.startswith(video_id) and file.endswith(".vtt"):
            vtt_path = os.path.join(DOCUMENTS_DIR, file)
            break

    if not vtt_path:
        raise HTTPException(status_code=404, detail="VTT subtitle file not found.")

    txt_path = os.path.join(DOCUMENTS_DIR, f"{video_id}.txt")
    convert_vtt_to_txt(vtt_path, txt_path, metadata or {})
    os.remove(vtt_path)
    return txt_path

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

    prompt = f"""If the question is a casual greeting or not related to the video (e.g., "Hi", "Hey", "What are you?", "How are you?", etc.), respond politely and say you're here to help with questions related to the video content.

    Otherwise:
    Answer the question using the following video transcript context. If the context is not sufficient, just say you don't have the answer.

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


@router.post("/chat_video")
def chat_with_video(data: ChatRequest, request: Request):
    if request.headers.get("x-api-key") != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    video_id = data.video_id
    transcript_path = os.path.join(DOCUMENTS_DIR, f"{video_id}.txt")

    if not os.path.exists(transcript_path):
        # Assume video_url and metadata come from client or DB (you can adjust)
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"📥 Transcript missing. Downloading subtitles for {video_id}...")
        try:
            download_and_transcribe(video_id, video_url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


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
