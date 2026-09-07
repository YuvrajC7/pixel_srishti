# 🌍 PIXEL-Srishti: Geospatial Auditing System

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)
![Next.js](https://img.shields.io/badge/Frontend-Next.js%20%7C%20React-black.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**PIXEL-Srishti** (developed for the **Smart India Hackathon 2026** - Ministry of Rural Development) is an AI-powered Decision Support System (DSS) designed to automatically audit MGNREGA projects, detect illegal construction, and track watershed development using satellite imagery.

By combining Optical and SAR (Synthetic Aperture Radar) data with a cutting-edge **Dual-Path Agentic Orchestrator**, PIXEL-Srishti allows government auditors to chat with satellite maps in plain English, operating entirely on edge devices (standard laptops) without requiring expensive cloud infrastructure.

---

## 🚀 Key Features

* **Dual-Path Agentic Orchestrator:** A master AI router that intercepts user queries. Uses **Groq (Llama-3-70B)** when online, and seamlessly falls back to a 100% offline **BART-MNLI Zero-Shot Router** if the internet drops.
* **SAR Compatibility:** Ingests Radar data to pierce through monsoon clouds, ensuring auditing never stops during the Indian rainy season.
* **VRAM Hot-Swapping:** A custom memory-management pipeline that dynamically loads and unloads heavy PyTorch models, allowing 5 massive neural networks to run locally on a single 8GB RTX 4060 laptop without Out-Of-Memory (OOM) crashes.
* **Hallucination-Free AI:** The LLM does not guess. It is strictly programmed to trigger deterministic mathematical vision models and only reads their raw output.

---

## 🧠 Machine Learning Architecture

Our backend relies on 4 specialist vision models, aggressively optimized for edge inference:

1. **Semantic Segmentation (`DeepLabV3+` with `ResNet34`)**
   * **Purpose:** Classifies every pixel to map urban spread and water bodies.
   * **Classes:** Background, Buildings, Woodlands, Water, Roads.
   * **Dataset:** Custom trained on LandCover.ai.
2. **Change Detection (`Siamese U-Net`)**
   * **Purpose:** Extracts deep features from "Before" and "After" satellite GeoTIFFs to highlight exact terrain/structural alterations (e.g., verifying if a pond was actually dug).
3. **Visual Question Answering (`BLIP-2 2.7B`)**
   * **Purpose:** Allows auditors to ask open-ended questions about the satellite image.
   * **Optimization:** Runs in `8-bit quantization` via `bitsandbytes` to drastically reduce memory overhead.
4. **Zero-Shot Object Detection (`Grounding DINO`)**
   * **Purpose:** Counts specific instances of unmapped objects (e.g., "houses", "water pumps", "tractors") using natural language prompts.

---

## 💻 Tech Stack

* **Backend / ML Engine:** Python, PyTorch, FastAPI, Hugging Face Transformers, OpenCV.
* **Frontend:** React / Next.js, Tailwind CSS.
* **Orchestration:** Groq API (Primary), BART-Large-MNLI (Offline Fallback).

---

## 🛠️ Installation & Setup

### Prerequisites
* NVIDIA GPU (RTX 4060 or equivalent recommended) for 8-bit model quantization.
* Python 3.10+ and Node.js.

### 1. Backend (Machine Learning Server)
```bash
# Clone the repository
git clone https://github.com/YuvrajC7/pixel_srishti.git
cd pixel_srishti/pixel_srishti_ml

# Install dependencies
pip install -r requirements.txt
```

**Download the Weights:** 
Run the following commands to automatically download our custom-trained weights from our **[Hugging Face Repository](https://huggingface.co/27Kushal/PIXEL-Srishti-Segmentation)** directly into your `checkpoints/` folder:

```bash
mkdir -p checkpoints
wget https://huggingface.co/27Kushal/PIXEL-Srishti-Segmentation/resolve/main/latest_seg_model.pth -O checkpoints/latest_seg_model.pth
wget https://huggingface.co/27Kushal/PIXEL-Srishti-Segmentation/resolve/main/latest_cd_model.pth -O checkpoints/latest_cd_model.pth
```

**Start the Server:**
```bash
# Export your Groq API key for the primary orchestrator
export GROQ_API_KEY="your-api-key-here"

# Start FastAPI
python api_server.py
```
*The ML backend will now be running on `http://localhost:8000`.*

> **To test offline mode:** Run `export SIMULATE_GROQ_FAILURE=true` before starting the server to force the offline BART-MNLI fallback router.

### 2. Frontend (Interactive Web GUI)
```bash
# Open a new terminal and navigate to the frontend folder
cd pixel_srishti/frontend

# Install dependencies and run
npm install
npm run dev
```
*The web interface will be accessible at `http://localhost:3000`.*

---

## 🔌 API Reference

The entire AI pipeline is exposed via a single, intelligent endpoint for the frontend to consume.

### `POST /api/chat`
**Description:** The Agentic Orchestrator handles routing automatically. Just send text and images.
* **Payload (FormData):**
  * `query`: (String) e.g., "Map the land cover." or "What changed between these images?"
  * `images`: (List[File]) 1 or 2 uploaded `.tiff` / `.jpg` files.
* **Response:**
  ```json
  {
      "status": "success",
      "agent_response": "Segmentation Results: Semantic segmentation analysis complete... | Mask generated at: temp_uploads/frontend_segmentation_mask.png"
  }
  ```

---

## 🧪 Testing Models Independently
To verify GPU compatibility without starting the API, run our interactive test script:
```bash
python test_playground.py
```

## 📄 License
This project is licensed under the **MIT License**.
