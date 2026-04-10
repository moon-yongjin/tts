from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import shutil
import glob

app = FastAPI()

# Enable CORS for the extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

INPUT_DIR = os.path.expanduser("~/Downloads/NB2_output")
COMPLETED_DIR = os.path.join(INPUT_DIR, "Completed")
os.makedirs(COMPLETED_DIR, exist_ok=True)

# Serve the input directory as static files so the extension can fetch images
app.mount("/images", StaticFiles(directory=INPUT_DIR), name="images")

@app.get("/next")
async def get_next_image():
    """
    Returns the next image to process.
    """
    files = [f for f in os.listdir(INPUT_DIR) 
             if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
             and os.path.isfile(os.path.join(INPUT_DIR, f))]
    
    first_file = files[0]
    prompt = None
    prompt_file = os.path.join(INPUT_DIR, f"{first_file}.prompt.txt")
    
    if os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read().replace("PROMPT: ", "").strip()
    
    return {
        "status": "ok", 
        "filename": first_file, 
        "url": f"http://localhost:8000/images/{first_file}",
        "prompt": prompt
    }

@app.post("/done/{filename}")
async def mark_as_done(filename: str):
    """
    Moves the processed image to the Completed folder.
    """
    src = os.path.join(INPUT_DIR, filename)
    if os.path.exists(src):
        shutil.move(src, os.path.join(COMPLETED_DIR, filename))
        
        # Also move associated prompt file if exists
        prompt_file = f"{filename}.prompt.txt"
        prompt_src = os.path.join(INPUT_DIR, prompt_file)
        if os.path.exists(prompt_src):
            shutil.move(prompt_src, os.path.join(COMPLETED_DIR, prompt_file))
            
        return {"status": "moved"}
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
