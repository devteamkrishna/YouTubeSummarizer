from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address
from webvtt import WebVTT
from app.utils.task_manager import active_tasks, cancel_existing_task, get_client_ip
import asyncio
from app.utils.embedder import embed_transcript
from chromadb import PersistentClient
from app.utils.summarizer import get_short_summary
from app.utils.cleanup import clear_chroma_embeddings, clear_old_transcripts
import re, os, shutil
from serpapi import GoogleSearch

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

DOCUMENTS_DIR = "documents"


# Request schema
class SearchRequest(BaseModel):
    topic: str


def is_youtube_url(text):
    return re.match(r"https?://(www\.)?(youtube\.com|youtu\.be)/", text)


def parse_duration(duration: str) -> int:
    parts = [int(p) for p in duration.split(":")]
    if len(parts) == 3:
        return parts[0]*3600 + parts[1]*60 + parts[2]
    elif len(parts) == 2:
        return parts[0]*60 + parts[1]
    elif len(parts) == 1:
        return parts[0]
    return 0


@router.post("/search_videos")
@limiter.limit("3/minute")
async def search_videos(payload: SearchRequest, request: Request, x_api_key: str = Header(None)):
    client_ip = get_client_ip(request)

    await cancel_existing_task(client_ip)

    current_task = asyncio.create_task(process_video_search(payload, x_api_key))
    active_tasks[client_ip] = current_task

    try:
        return await current_task
    except asyncio.CancelledError:
        print(f"⏹ Task cancelled by new request from {client_ip}")
        raise HTTPException(status_code=499, detail="Request cancelled")


async def process_video_search(payload: SearchRequest, x_api_key: str):
    try:
        print("\n🔍 Started Searching Process...\n")
        if x_api_key != API_KEY:
            raise HTTPException(status_code=403, detail="Invalid or missing API Key")

        query = payload.topic.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Topic is required.")

        clear_chroma_embeddings()
        clear_old_transcripts()

        # Use SerpApi SDK for YouTube video search
        params = {
            "engine": "youtube",
            "search_query": query,
            "hl": "en",
            "sp": "EgYQARgDKAE%253D",  # Filter (e.g., CC)
            "api_key": SERPAPI_KEY,
            "num": 10
        }

        try:
            search = GoogleSearch(params)
            serp_data = search.get_dict()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"SerpApi error: {str(e)}")

        serp_results = serp_data.get("video_results", [])
        if not serp_results:
            raise HTTPException(status_code=404, detail="No videos found.")

        # Filter top 3 valid videos
        selected = []
        for video in serp_results:
            # print(f"\n{video}\n")
            if "CC" not in video.get("extensions", []):
                continue
            duration = parse_duration(video.get("length", "0:00"))
            if duration > 900:
                continue
            selected.append((video["link"], video, duration))
            if len(selected) == 3:
                break

        if not selected:
            raise HTTPException(status_code=404, detail="No valid videos with subtitles found.")

        videos = []

        for video_url, metadata, duration in selected:
            video_id = video_url.split("v=")[-1]

            videos.append({
                "title": metadata.get("title"),
                "vid_id": video_id,
                "summary": get_short_summary(metadata.get("title", ""), metadata.get("description", "")),
                "channel": metadata.get("channel", {}).get("name", "Unknown"),
                "duration_seconds": duration,
                "iframe": f"https://www.youtube.com/embed/{video_id}"
            })

        print("✅ Returning", len(videos), "videos")
        return {"videos": videos}
    
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
