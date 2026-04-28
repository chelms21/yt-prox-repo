from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import logging

# Set up logging so you can see errors in the Render dashboard
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

INSTANCES = [
    "https://inv.tux.rs",
    "https://invidious.nerdvpn.de",
    "https://iv.melmac.space",
    "https://invidious.projectsegfau.lt"
]

@app.get("/extract")
def extract_m3u8(url: str):
    video_id = ""
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
    else:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL format")

    for instance in INSTANCES:
        try:
            api_url = f"{instance}/api/v1/videos/{video_id}"
            logger.info(f"Trying instance: {instance}")
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Priority 1: HLS URL (Best for Live Streams)
                hls_url = data.get("hlsUrl")
                if hls_url:
                    return {"url": hls_url, "title": data.get("title")}
                
                # Priority 2: Adaptive Formats (Best for regular videos)
                adaptive = data.get("adaptiveFormats")
                if adaptive:
                    # Filter for video+audio or just high quality
                    return {"url": adaptive[-1]["url"], "title": data.get("title")}

        except Exception as e:
            logger.error(f"Instance {instance} failed: {str(e)}")
            continue 

    raise HTTPException(status_code=500, detail="All Invidious instances failed. YouTube might be blocking them.")
