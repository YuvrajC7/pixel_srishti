import os
from transformers import pipeline

# Import our PyTorch Agent Tools
from tools.agent_tools import (
    tool_detect_change,
    tool_answer_vqa,
    tool_segment_image,
    tool_detect_objects
)

print("[Fallback Orchestrator] Loading BART-MNLI for offline zero-shot routing...")
# Load to CPU (device=-1) to save GPU VRAM for the actual specialist models
zero_shot_classifier = pipeline(
    "zero-shot-classification", 
    model="facebook/bart-large-mnli", 
    device=-1
)
print("[Fallback Orchestrator] BART-MNLI loaded successfully.")

# Map semantic labels to the actual tools
LABEL_TO_TOOL = {
    "detect changes or differences between two images": "change_detection",
    "segment map classify land cover types like water buildings woodlands": "segmentation",
    "answer a descriptive question about the scene": "vqa",
    "highlight count or locate specific objects": "object_detection"
}

def run_fallback_orchestrator(user_query: str, uploaded_images: list[str]) -> str:
    """
    Offline fallback path using BART-MNLI zero-shot classification.
    Only triggers if Groq fails. No multi-tool sequencing, basic parameter mapping.
    """
    if not uploaded_images:
        return "[Fallback System] Error: No images provided."
        
    candidate_labels = list(LABEL_TO_TOOL.keys())
    
    # 1. Zero-Shot Intent Classification
    result = zero_shot_classifier(user_query, candidate_labels)
    best_label = result['labels'][0]
    selected_tool = LABEL_TO_TOOL[best_label]
    
    print(f"[Fallback Orchestrator] Query matched to: '{selected_tool}' (Confidence: {result['scores'][0]:.2f})")
    
    # 2. Rule-based Execution & Templated Response
    try:
        if selected_tool == "segmentation":
            # Assume first image
            img_path = uploaded_images[0]
            res_text, mask_path = tool_segment_image(img_path)
            return (
                f"[OFFLINE FALLBACK MODE] Triggered Land Cover Segmentation.\n"
                f"Analysis: {res_text}\n"
                f"Generated Map: {mask_path}"
            )
            
        elif selected_tool == "change_detection":
            # Assume first two images are provided
            if len(uploaded_images) < 2:
                return "[OFFLINE FALLBACK MODE] Error: Change detection requires 2 images."
            img_a, img_b = uploaded_images[0], uploaded_images[1]
            res_text, mask_path = tool_detect_change(img_a, img_b)
            return (
                f"[OFFLINE FALLBACK MODE] Triggered Change Detection.\n"
                f"Analysis: {res_text}\n"
                f"Generated Map: {mask_path}"
            )
            
        elif selected_tool == "object_detection":
            # Pass the raw query directly (no LLM parameter extraction)
            img_path = uploaded_images[0]
            res = tool_detect_objects(img_path, user_query)
            return (
                f"[OFFLINE FALLBACK MODE] Triggered Object Detection.\n"
                f"System searched for '{user_query}' and found {res['count']} instances."
            )
            
        elif selected_tool == "vqa":
            # Pass the raw query directly
            img_path = uploaded_images[0]
            answer = tool_answer_vqa(img_path, user_query)
            return (
                f"[OFFLINE FALLBACK MODE] Triggered Visual Question Answering.\n"
                f"Answer: {answer}"
            )
            
    except Exception as e:
        return f"[OFFLINE FALLBACK MODE] Internal Tool Error: {str(e)}"
