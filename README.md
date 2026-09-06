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
