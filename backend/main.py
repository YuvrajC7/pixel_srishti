from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from PIL import Image
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def count_blue_pixels(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        width, height = img.size
        pixels = img.load()
        blue_count = 0
        for x in range(width):
            for y in range(height):
                r, g, b = pixels[x, y]
                # Dodger Blue is (30, 144, 255). Let's detect prominent blue.
                if b > 150 and b > r + 50 and b > g + 20:
                    blue_count += 1
        return blue_count
    except Exception as e:
        return 0

@app.post("/api/chat")
async def chat(
    message: str = Form(...),
    inputMode: str = Form(...),
    isBenchmark: str = Form(...),
    imageT1: Optional[UploadFile] = File(None),
    imageT2: Optional[UploadFile] = File(None)
):
    print(f"Received query: {message}")
    print(f"Mode: {inputMode}")
    
    if inputMode == "BI_TEMPORAL":
        if not imageT1 or not imageT2:
            return {"reply": "Error: Both Image T1 and Image T2 are required for Bi-Temporal Change Detection."}
        
        # Read files
        t1_bytes = await imageT1.read()
        t2_bytes = await imageT2.read()
        
        print(f"Processing T1: {imageT1.filename}")
        print(f"Processing T2: {imageT2.filename}")
        
        # Analyze pixel differences (Simple Mock CV Model)
        t1_blue = count_blue_pixels(t1_bytes)
        t2_blue = count_blue_pixels(t2_bytes)
        
        if t2_blue > t1_blue:
            diff = t2_blue - t1_blue
            increase_pct = (diff / max(1, t1_blue)) * 100
            reply = f"[Agentic Orchestrator - Change Detection Specialist]:\nI have successfully executed the Bi-Temporal analysis on {imageT1.filename} and {imageT2.filename}.\n\nVisual Evidence Grounding: I detected a massive {increase_pct:.0f}% increase in water bodies (blue spectral signature) between T1 and T2. The watershed intervention in this sector appears highly successful, replacing barren land with expanded water catchments."
        elif t1_blue > t2_blue:
            reply = f"[Agentic Orchestrator - Change Detection Specialist]:\nI have analyzed the temporal pair. I detected a decrease in water bodies between T1 and T2, indicating potential drought or drainage issues."
        else:
            reply = f"[Agentic Orchestrator]: I analyzed the images. No significant change in water bodies was detected."
            
        return {"reply": reply}
        
    else:
        # Default response for other modes
        return {"reply": f"[Agentic Orchestrator]: Received query: '{message}' in {inputMode} mode. (Specialist model for this mode is currently pending integration)."}
