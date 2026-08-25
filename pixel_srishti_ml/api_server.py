import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import our VRAM-optimized Agent Tools
from tools.agent_tools import tool_detect_change, tool_answer_vqa, tool_segment_image, tool_detect_objects
from tools.orchestrator_main import run_smart_agent

app = FastAPI(
    title="Jaldrishti ML Backend", 
    description="Offline REST API for the SIH 2026 Presentation (Runs on RTX 4060)",
    version="1.0"
)

# Enable CORS so the JS frontend can make requests from localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production you'd restrict this, but * is fine for a local demo
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post("/api/detect_change")
async def api_detect_change(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...)
):
    """
    Endpoint for identifying infrastructure/water body changes between two SAR/Optical images.
    """
    try:
        path1 = os.path.join(TEMP_DIR, image1.filename)
        path2 = os.path.join(TEMP_DIR, image2.filename)
        
        with open(path1, "wb") as buffer:
            shutil.copyfileobj(image1.file, buffer)
        with open(path2, "wb") as buffer:
            shutil.copyfileobj(image2.file, buffer)
            
        # Run our Agent Tool (which loads the model, infers, and clears VRAM instantly)
        result = tool_detect_change(path1, path2)
        
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ask_question")
async def api_ask_question(
    image: UploadFile = File(...),
    question: str = Form(...)
):
    """
    Endpoint for answering specific queries (VQA) like "How many new houses?"
    """
    try:
        path = os.path.join(TEMP_DIR, image.filename)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        # Run VQA Tool (Loads BLIP-2 + Grounding DINO, infers, clears VRAM)
        answer = tool_answer_vqa(path, question)
        
        return {"status": "success", "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/segment")
async def api_segment(
    image: UploadFile = File(...)
):
    """
    Endpoint for LandCover.ai Semantic Segmentation (Woodlands, Water, Buildings, Roads).
    """
    try:
        path = os.path.join(TEMP_DIR, image.filename)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        # Run Segmentation Tool (Loads DeepLabV3+, infers, clears VRAM)
        result_text, mask_path = tool_segment_image(path)
        
        return {"status": "success", "description": result_text, "mask_path": mask_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/detect_objects")
async def api_detect_objects(
    image: UploadFile = File(...),
    query: str = Form(...)
):
    """
    Endpoint for Zero-Shot Object Detection using Grounding DINO.
    Pass a query like 'houses' or 'water pump' to get bounding boxes.
    """
    try:
        path = os.path.join(TEMP_DIR, image.filename)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        # Run Object Detection Tool (Loads Grounding DINO, infers, clears VRAM)
        result = tool_detect_objects(path, query)
        
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from typing import List

@app.post("/api/chat")
async def api_chat(
    query: str = Form(...),
    images: List[UploadFile] = File(default=[])
):
    """
    Master Agentic Endpoint. 
    Frontend just sends the user's natural language query and any uploaded images.
    The Backend Orchestrator automatically handles tool routing, fallback, and synthesis.
    """
    try:
        saved_paths = []
        for img in images:
            path = os.path.join(TEMP_DIR, img.filename)
            with open(path, "wb") as buffer:
                shutil.copyfileobj(img.file, buffer)
            saved_paths.append(path)
            
        # Run Master Wrapper (Groq -> Fallback to Offline)
        final_answer = run_smart_agent(query, saved_paths)
        
        return {"status": "success", "agent_response": final_answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "gpu_ready": True}

if __name__ == "__main__":
    print("Starting Jaldrishti ML Backend on http://localhost:8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
