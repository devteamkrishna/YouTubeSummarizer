# YT Script Clone

`YT Script Clone` is a FastAPI application that helps users find short YouTube videos on a topic, generate quick AI summaries, and ask questions about a selected video using transcript-based RAG.

The project combines:

- `FastAPI` for the backend and HTML delivery
- `SerpApi` for YouTube discovery
- `yt-dlp` + `webvtt-py` for subtitle retrieval and transcript extraction
- `SentenceTransformers` + `ChromaDB` for embeddings and retrieval
- `Groq` for video summaries and chat answers

## Features

- Search for YouTube videos by topic
- Filter videos to short-form results with closed captions
- Generate 4-point summaries from title and description
- Ask follow-up questions about a selected video
- Build transcript embeddings on demand
- Clear cached transcripts and embeddings before a new search
- Basic rate limiting on search requests

## Project Structure

```text
YT_Script_clone/
├── app/
│   ├── main.py                # FastAPI app entrypoint
│   ├── routes/
│   │   ├── home.py            # Landing page
│   │   ├── search_02.py       # Active search endpoint
│   │   ├── chat.py            # Video Q&A endpoint
│   │   ├── search.py          # Older subtitle-download search flow
│   │   └── search_agent.py    # Experimental LangChain-based search
│   ├── templates/             # Jinja2 HTML templates
│   ├── assets/                # CSS, JS, images
│   └── utils/                 # Embedding, cleanup, task management, summaries
├── chroma_db/                 # Persistent vector store
├── documents/                 # Downloaded/generated transcript text files
├── rag/                       # Additional RAG helpers
├── requirements.txt
└── Dockerfile
```

## How It Works

1. A user enters a topic on the landing page.
2. `POST /search_videos` uses SerpApi to find candidate YouTube videos.
3. Results are filtered to videos with CC and duration under 15 minutes.
4. Groq generates a short 4-point summary for each returned video.
5. When the user asks a question, `POST /chat_video` ensures the transcript exists.
6. The transcript is chunked, embedded, stored in ChromaDB, and queried for relevant context.
7. Groq answers the question using the retrieved transcript chunks.

## Requirements

- Python `3.11+`
- A working internet connection for external APIs
- API keys for:
  - Groq
  - SerpApi
  - The app's internal request header authentication

## Environment Variables

Create a `.env` file in the project root:

```env
API_KEY=your_internal_api_key
GROQ_API_KEY=your_groq_api_key
SERPAPI_KEY=your_serpapi_key
```

### Variable Notes

- `API_KEY`: checked against the `x-api-key` request header
- `GROQ_API_KEY`: used for both summaries and chat answers
- `SERPAPI_KEY`: used by the active `/search_videos` route

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Locally

Use the FastAPI app module directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8012
```

Then open:

```text
http://127.0.0.1:8012
```

## API Endpoints

### `GET /`

Serves the main HTML interface.

### `POST /search_videos`

Searches YouTube and returns up to 3 short captioned videos.

Request body:

```json
{
  "topic": "python fastapi tutorial"
}
```

Required header:

```http
x-api-key: <API_KEY>
```

Example response shape:

```json
{
  "videos": [
    {
      "title": "Video title",
      "vid_id": "youtube_video_id",
      "summary": "Point 1: ...",
      "channel": "Channel name",
      "duration_seconds": 420,
      "iframe": "https://www.youtube.com/embed/youtube_video_id"
    }
  ]
}
```

### `POST /chat_video`

Answers a question about a selected YouTube video using transcript retrieval.

Request body:

```json
{
  "video_id": "youtube_video_id",
  "query": "What are the main takeaways?"
}
```

Required header:

```http
x-api-key: <API_KEY>
```

Example response:

```json
{
  "answer": "..."
}
```

## Frontend Notes

- The landing page is rendered from `app/templates/index-main.html`.
- Client-side logic lives in `app/assets/js/search.js`.
- The frontend currently sends requests with a hard-coded `x-api-key` value in JavaScript, so you may want to replace that with a safer configuration approach before production use.

## Data and Storage

- `documents/` stores downloaded subtitle transcripts converted to `.txt`
- `chroma_db/` stores persistent embeddings for transcript chunks
- Search cleanup removes previous transcripts and existing embeddings before new searches

## Known Codebase Notes

- The active search route is `app/routes/search_02.py`, not `app/routes/search.py`.
- The `Dockerfile` currently starts `uvicorn main:app`, but the application entrypoint in this repository is `app.main:app`.
- `search_agent.py` appears to be experimental and is not included by `app/main.py`.

## Docker

The included `Dockerfile` needs a small entrypoint adjustment to match the current app layout. A working run command is:

```bash
docker build -t yt-script-clone .
docker run --env-file .env -p 8012:8012 yt-script-clone uvicorn app.main:app --host 0.0.0.0 --port 8012
```

## Future Improvements

- Move the frontend API key out of client-side JavaScript
- Add transcript caching per video instead of clearing all previous data
- Add tests for search and chat routes
- Improve Docker configuration
- Add request/response examples to OpenAPI docs

## License

No license file is currently included in this repository. Add one if you plan to distribute or open-source the project.
