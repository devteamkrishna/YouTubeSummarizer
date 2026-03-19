from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from yt_dlp import YoutubeDL
import os
import shutil
from dotenv import load_dotenv
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from webvtt import WebVTT
from app.utils.task_manager import active_tasks, cancel_existing_task, get_client_ip
import asyncio
from app.utils.embedder import embed_transcript
from chromadb import PersistentClient
from app.utils.summarizer import get_short_summary


limiter = Limiter(key_func=get_remote_address)


load_dotenv()
API_KEY = os.getenv("API_KEY")

router = APIRouter()

DOCUMENTS_DIR = "documents"

# 🔧 Input schema
class SearchRequest(BaseModel):
    topic: str


from webvtt import WebVTT

def convert_vtt_to_txt(vtt_path: str, txt_path: str):
    """
    Converts a VTT file to a plain text file with deduplication.
    Args:
        vtt_path (str): Path to the .vtt file.
        txt_path (str): Path to save the output .txt file.
    """
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

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        print(f"[✅] Transcript saved to: {txt_path}")

    except Exception as e:
        print(f"[❌] Failed to convert VTT to TXT: {e}")


@router.post("/search_videos")
@limiter.limit("3/minute")
async def search_videos(payload: SearchRequest, request: Request, x_api_key: str = Header(None)):
    client_ip = get_client_ip(request)

    # Cancel any ongoing task
    await cancel_existing_task(client_ip)

    # Create a new task and track it
    current_task = asyncio.create_task(process_video_search(payload, x_api_key))
    active_tasks[client_ip] = current_task

    try:
        return await current_task
    except asyncio.CancelledError:
        print(f"⏹ Task cancelled by new request from {client_ip}")
        raise HTTPException(status_code=499, detail="Request cancelled")


async def process_video_search(payload: SearchRequest, x_api_key: str):
    
    print("\n Started Searching Process ... \n")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API Key")
    
    try:
        query = payload.topic.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Topic is required.")
        
        # 🔥 Delete all previous embeddings
        client = PersistentClient(path="./chroma_db")
        collection = client.get_or_create_collection(name="youtube_videos")
        all_docs = collection.get(include=[])  # Just fetch IDs
        all_ids = all_docs.get("ids", [])

        if all_ids:
            collection.delete(ids=all_ids)
            print(f"✅ Deleted {len(all_ids)} embeddings.")
        else:
            print("✅ No embeddings to delete.")
        print("🧹 All previous embeddings deleted.")

        # 🧹 Clear old transcriptions
        if os.path.exists(DOCUMENTS_DIR):
            shutil.rmtree(DOCUMENTS_DIR)
        os.makedirs(DOCUMENTS_DIR, exist_ok=True)

        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "format": "best",
            "default_search": "ytsearch5",
            "extract_flat": False,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "outtmpl": f"{DOCUMENTS_DIR}/%(id)s.%(ext)s",
        }

        videos = []
        with YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(query, download=False)
            entries = search_results.get("entries", [])

            # for idx, entry in enumerate(entries):
            print("🔍 Total entries received:", len(entries))
            valid_count = 0
            for i, entry in enumerate(entries, 1):
                if valid_count >= 3:
                    break

                title = entry.get("title", "")
                duration = entry.get("duration", 0)
                video_id = entry.get("id", "")

                print(f"🔍 Checking: {title} ({duration}s)")

                if duration > 900:
                    print(f"⏩ Skipped (too long): {duration}s")
                    continue

                try:
                    ydl.download([entry["webpage_url"]])
                except Exception as e:
                    print(f"[❌] Failed to download subtitles for {video_id}: {e}")
                    continue

                # Check if .vtt file exists
                # vtt_found = False
                # for file in os.listdir(DOCUMENTS_DIR):
                #     if file.startswith(video_id) and file.endswith(".vtt"):
                #         vtt_found = True
                #         break

                # if not vtt_found:
                #     print(f"[❌] Skipped: No English subtitles found for {video_id}")
                #     continue
                # 🔍 Convert .vtt to clean .txt only if exists
                vtt_found = False
                for file in os.listdir(DOCUMENTS_DIR):
                    if file.startswith(video_id) and file.endswith(".vtt"):
                        vtt_found = True
                        old_path = os.path.join(DOCUMENTS_DIR, file)
                        new_path = os.path.join(DOCUMENTS_DIR, f"{video_id}.txt")

                        try:
                            convert_vtt_to_txt(old_path, new_path)
                            print(f"[✅] Transcript saved to: {new_path}")
                        except Exception as e:
                            print(f"Conversion error for {video_id}: {e}")
                            continue  # Skip video if conversion fails

                        os.remove(old_path)  # clean up .vtt
                        break  # found and converted, exit loop

                if not vtt_found:
                    print(f"[❌] Skipped: No English subtitles found for {video_id}")
                    continue  # skip this video


                print(f"📥 [{valid_count+1}/3] Accepted: {title}")

                videos.append({
                    "title": title,
                    "vid_id": video_id,
                    "summary": get_short_summary(title, entry.get("description", "")),
                    "channel": entry.get("uploader", "Unknown"),
                    "duration_seconds": duration,
                    "iframe": f"https://www.youtube.com/embed/{video_id}"
                })

                valid_count += 1

            # for i, entry in enumerate(entries[:3], 1):
            #     if len(videos) >= 3:
            #         break

            #     print(f"📥 [{i}/3] Fetching: {entry.get('title')}")

            #     duration = entry.get("duration", 0)
            #     if duration > 900:  # >15 min
            #         continue

            #     video_id = entry["id"]
            #     title = entry.get("title", "")
            #     description = entry.get("description", "")

            #     summary = ""
            #     try:
            #         summary = get_short_summary(title, description)
            #     except Exception as e:
            #         print(f"[⚠️] Summary generation failed for {video_id}: {e}")
                
            #     channel = entry.get("uploader", "Unknown Channel")
            #     duration = entry.get("duration", 0)
            #     iframe = f"https://www.youtube.com/embed/{video_id}"


            #     # 📝 Try downloading transcript
            #     try:
            #         ydl.download([entry["webpage_url"]])
            #     except Exception as e:
            #         print(f"Transcript error for {video_id}: {e}")    

            #     # 🔍 Convert .vtt to clean .txt
            #     for file in os.listdir(DOCUMENTS_DIR):
            #         if file.startswith(video_id) and file.endswith(".vtt"):
            #             old_path = os.path.join(DOCUMENTS_DIR, file)
            #             new_path = os.path.join(DOCUMENTS_DIR, f"{video_id}.txt")
                        
            #             try:
            #                 convert_vtt_to_txt(old_path, new_path)
            #             except Exception as e:
            #                 print(f"Conversion error: {e}")
                        
            #             os.remove(old_path)

            #             # Embed and store
            #             try:
            #                 embed_result = embed_transcript(video_id, new_path)
            #                 if embed_result:
            #                     print(embed_result.get("message"))
            #             except Exception as e:
            #                 print(f"Embedding error for {video_id}: {e}")

            #     print(f"✅ [{i+1}/3] Done: Transcript saved in Documents")

                # videos.append({
                #     "title": title,
                #     "vid_id": video_id,
                #     "summary": summary,
                #     "channel": channel,
                #     "duration_seconds": duration,
                #     "iframe": iframe
                # })

        return {"videos": videos}
    
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
