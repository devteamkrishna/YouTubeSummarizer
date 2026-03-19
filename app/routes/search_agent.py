from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.utils.task_manager import active_tasks, cancel_existing_task, get_client_ip
from app.utils.cleanup import clear_chroma_embeddings, clear_old_transcripts
from langchain.agents import Tool, initialize_agent
from langchain.agents.agent_types import AgentType
from serpapi import GoogleSearch
import re, os, asyncio
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Request schema
class SearchRequest(BaseModel):
    topic: str

# --- Tool Functions ---
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

def search_youtube_videos(topic: str):
    params = {
        "engine": "youtube",
        "search_query": topic,
        "hl": "en",
        "sp": "EgYQARgDKAE%253D",  # CC filter
        "api_key": SERPAPI_KEY,
        "num": 10
    }
    search = GoogleSearch(params)
    return search.get_dict().get("video_results", [])

def filter_valid_videos(serp_results):
    selected = []
    for video in serp_results:
        if "CC" not in video.get("extensions", []):
            continue
        duration = parse_duration(video.get("length", "0:00"))
        if duration > 900:
            continue
        selected.append((video["link"], video, duration))
        if len(selected) == 3:
            break
    return selected

def summarize_metadata(title, description):
    from app.utils.summarizer import get_short_summary
    return get_short_summary(title, description)

def cleanup_data():
    clear_chroma_embeddings()
    clear_old_transcripts()
    return "✅ Cleanup completed"

# --- LangChain Tool Setup ---
tools = [
    Tool(name="YouTubeSearch", func=search_youtube_videos, description="Search for YouTube videos by topic"),
    Tool(name="FilterVideos", func=filter_valid_videos, description="Filter videos under 15min with CC"),
    Tool(name="SummarizeVideo", func=lambda x: summarize_metadata(x["title"], x["description"]), description="Summarize title and description"),
    Tool(name="Cleanup", func=cleanup_data, description="Clear embeddings and transcript cache")
]

llm = ChatGroq(
    model="meta-llama/llama-4-maverick-17b-128e-instruct",
    temperature=0.4,
)

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# --- FastAPI Route ---
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

# --- Agentic Video Search ---
# async def process_video_search(payload: SearchRequest, x_api_key: str):
#     try:
#         print("\n🔍 Started Agentic Video Search...\n")
#         if x_api_key != API_KEY:
#             raise HTTPException(status_code=403, detail="Invalid or missing API Key")

#         topic = payload.topic.strip()
#         if not topic:
#             raise HTTPException(status_code=400, detail="Topic is required.")

#         # Run cleanup
#         cleanup_data()

#         # Run agent steps manually
#         serp_results = search_youtube_videos(topic)
#         selected = filter_valid_videos(serp_results)

#         if not selected:
#             raise HTTPException(status_code=404, detail="No valid videos found.")

#         videos = []
#         for video_url, metadata, duration in selected:
#             video_id = video_url.split("v=")[-1]
#             videos.append({
#                 "title": metadata.get("title"),
#                 "vid_id": video_id,
#                 "summary": summarize_metadata(metadata.get("title", ""), metadata.get("description", "")),
#                 "channel": metadata.get("channel", {}).get("name", "Unknown"),
#                 "duration_seconds": duration,
#                 "iframe": f"https://www.youtube.com/embed/{video_id}"
#             })

#         return {"videos": videos}

#     except Exception as e:
#         print(f"Error: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

async def process_video_search(payload: SearchRequest, x_api_key: str):
    try:
        print("\n🔍 Started Agentic Video Search...\n")
        if x_api_key != API_KEY:
            raise HTTPException(status_code=403, detail="Invalid or missing API Key")

        topic = payload.topic.strip()
        if not topic:
            raise HTTPException(status_code=400, detail="Topic is required.")

        cleanup_data()
        result = agent.run(f"Find 3 short YouTube videos with closed captions about: {topic}. Summarize them.")

        return {"result": result}
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))