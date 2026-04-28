from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# List of public Invidious instances as backups
INSTANCES = [
    "https://inv.tux.rs",
    "https://invidious.nerdvpn.de",
    "https://iv.melmac.space",
    "https://invidious.jing.rocks"
]

@app.get("/extract")
def extract_m3u8(url: str):
    # 1. Extract Video ID (works for youtube.com/watch?v=ID or youtu.be/ID)
    video_id = ""
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
    else:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    # 2. Try instances until one works
    for instance in INSTANCES:
        try:
            api_url = f"{instance}/api/v1/videos/{video_id}"
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Invidious provides a direct HLS (m3u8) URL for lives
                if data.get("liveNow") or "hlsUrl" in data:
                    return {
                        "url": data.get("hlsUrl"),
                        "title": data.get("title"),
                        "instance_used": instance
                    }
                else:
                    # If it's a normal video, we look for the highest quality adaptive stream
                    return {"url": data["formatStreams"][-1]["url"], "title": data["title"]}
                    
        except Exception:
            continue # Try the next instance if one fails

    raise HTTPException(status_code=500, detail="All Invidious instances failed to fetch this video.")
