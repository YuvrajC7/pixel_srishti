import os
import torch
import numpy as np
import cv2
from PIL import Image
import torchvision.transforms as T

# Import your trained flagship Siamese architecture
from models.siamese_unet import SiameseUNet

def clean_mask_noise(mask_array, min_pixel_area=40):
    """
    Removes scattered salt-and-pepper noise so only real, 
    cohesive structural changes are kept.
    """
    mask_uint8 = (mask_array * 255).astype(np.uint8)
    
    # 1. Morphological opening to eliminate tiny speckles
    kernel = np.ones((3, 3), np.uint8)
    opened = cv2.morphologyEx(mask_uint8, cv2.MORPH_OPEN, kernel)
    
    # 2. Filter out tiny connected blobs smaller than min_pixel_area
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(opened)
    cleaned = np.zeros_like(opened)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_pixel_area:
            cleaned[labels == i] = 1
            
    return cleaned

def generate_change_description(mask_array):
    """Generates an informative, dynamic text summary based on cleaned pixels."""
    total_pixels = mask_array.size
    changed_pixels = np.sum(mask_array > 0)
    change_ratio = (changed_pixels / total_pixels) * 100
    
    if change_ratio < 0.5:
        return f"No significant structural change detected ({change_ratio:.2f}% variance, likely minor seasonal/lighting differences)."
    elif change_ratio < 5.0:
        return f"Localized structural change detected ({change_ratio:.2f}% of area). Detected localized ground excavation, path clearance, or small-scale civil work."
    elif change_ratio < 15.0:
        return f"Moderate terrain alteration detected ({change_ratio:.2f}% of area). Indicates land clearance, new road extension, or pond excavation."
    else:
        return f"Substantial geographic change detected! ({change_ratio:.2f}% of region altered). High likelihood of major civil works or water accumulation."

def tool_detect_change(img_A_path, img_B_path, checkpoint_path="checkpoints/latest_cd_model.pth"):
    """
    Tool for detecting structural changes between two satellite captures.
    Loads Siamese U-Net, runs inference, cleans noise, saves transparent RGBA overlay, and clears VRAM.
    """
    print("[Agent Tool] Running Change Detection...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 1. Load Model
    model = SiameseUNet().to(device)
    if os.path.exists(checkpoint_path):
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
    else:
        print(f"[Warning] Checkpoint '{checkpoint_path}' not found! Using initialized weights.")
    
    model.eval()

    # 2. Transform Images
    transform = T.Compose([
        T.Resize((512, 512)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    img_A = Image.open(img_A_path).convert('RGB')
    img_B = Image.open(img_B_path).convert('RGB')
    orig_size = img_A.size 
    
    t_A = transform(img_A).unsqueeze(0).to(device)
    t_B = transform(img_B).unsqueeze(0).to(device)

    # 3. Inference
    with torch.no_grad():
        output = model(t_A, t_B)
        raw_mask = (torch.sigmoid(output) > 0.5).cpu().numpy().squeeze()

    # 4. Clean up noise speckles
    cleaned_mask = clean_mask_noise(raw_mask, min_pixel_area=40)

    # 5. Generate Natural Language Text
    nl_answer = generate_change_description(cleaned_mask)

    # 6. Save as TRANSPARENT RGBA mask (fixes the solid black box overlay!)
    h, w = cleaned_mask.shape
    rgba_mask = np.zeros((h, w, 4), dtype=np.uint8)
    
    # Changed pixels: Semi-transparent glowing red (R=255, G=35, B=35, Alpha=190)
    rgba_mask[cleaned_mask > 0] = [255, 35, 35, 190]
    # Unchanged pixels remain [0, 0, 0, 0] (100% transparent so map is visible)

    mask_img = Image.fromarray(rgba_mask, mode="RGBA")
    mask_img = mask_img.resize(orig_size, Image.NEAREST)
    output_mask_path = "frontend_output_mask.png"
    mask_img.save(output_mask_path)

    # 7. VRAM SAVING HACK
    del model
    torch.cuda.empty_cache()

    return nl_answer, output_mask_path


def tool_segment_image(img_path, checkpoint_path="checkpoints/latest_seg_model.pth"):
    """
    Tool for segmenting land cover (Water, Buildings, Woodlands, Roads).
    Uses DeepLabV3+ with ResNet34 backbone, infers, saves transparent RGBA colored mask, and clears VRAM.
    """
    print("[Agent Tool] Running DeepLabV3+ Segmentation...")
    import segmentation_models_pytorch as smp
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Initialize model with 5 classes as trained
    model = smp.DeepLabV3Plus(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=3,
        classes=5,
    ).to(device)
    
    if os.path.exists(checkpoint_path):
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
    else:
        print(f"[Warning] DeepLabV3+ checkpoint '{checkpoint_path}' not found! Using initialized weights.")
        
    model.eval()
    
    # Prepare Image
    transform = T.Compose([
        T.Resize((512, 512)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    img = Image.open(img_path).convert('RGB')
    orig_size = img.size 
    t_img = transform(img).unsqueeze(0).to(device)
    
    # Inference
    with torch.no_grad():
        output = model(t_img)
        pred_mask = torch.argmax(output, dim=1).squeeze().cpu().numpy()
        
    # Generate statistics for the LLM Agent
    total_pixels = pred_mask.size
    pct_buildings = (np.sum(pred_mask == 1) / total_pixels) * 100
    pct_woodlands = (np.sum(pred_mask == 2) / total_pixels) * 100
    pct_water = (np.sum(pred_mask == 3) / total_pixels) * 100
    pct_roads = (np.sum(pred_mask == 4) / total_pixels) * 100
    
    nl_answer = (
        f"Semantic segmentation analysis complete. Area breakdown:\n"
        f"- Buildings: {pct_buildings:.2f}%\n"
        f"- Woodlands: {pct_woodlands:.2f}%\n"
        f"- Water Bodies: {pct_water:.2f}%\n"
        f"- Roads/Trails: {pct_roads:.2f}%"
    )
    
    # Transparent RGBA color map:
    # 0: Background -> 100% transparent [0, 0, 0, 0]
    # 1: Buildings  -> Bright Red with opacity [239, 68, 68, 180]
    # 2: Woodlands  -> Forest Green with opacity [34, 197, 94, 180]
    # 3: Water      -> Blue with opacity [59, 130, 246, 190]
    # 4: Roads      -> Light Gray with opacity [203, 213, 225, 180]
    color_map_rgba = np.array([
        [0, 0, 0, 0],
        [239, 68, 68, 180],
        [34, 197, 94, 180],
        [59, 130, 246, 190],
        [203, 213, 225, 180]
    ], dtype=np.uint8)
    
    colored_mask = color_map_rgba[pred_mask]
    
    mask_img = Image.fromarray(colored_mask, mode="RGBA")
    mask_img = mask_img.resize(orig_size, Image.NEAREST)
    output_mask_path = "frontend_segmentation_mask.png"
    mask_img.save(output_mask_path)
    
    # VRAM SAVING HACK
    del model
    torch.cuda.empty_cache()
    
    return nl_answer, output_mask_path


def tool_detect_objects(img_path, query_prompt):
    """
    Tool for zero-shot object detection using Grounding DINO.
    Finds bounding boxes for specific items (e.g. 'houses', 'tractors', 'ponds').
    """
    print(f"[Agent Tool] Running Grounding DINO for '{query_prompt}'...")
    from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model_id = "IDEA-Research/grounding-dino-base"
    
    # 1. Load Model
    processor = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id).to(device)
    model.eval()
    
    # 2. Prepare Image and Text
    image = Image.open(img_path).convert("RGB")
    query_prompt = query_prompt.lower()
    if not query_prompt.endswith("."):
        query_prompt += "."
        
    inputs = processor(images=image, text=query_prompt, return_tensors="pt").to(device)
    
    # 3. Inference
    with torch.no_grad():
        outputs = model(**inputs)
        
    target_sizes = torch.tensor([image.size[::-1]])
    results = processor.image_processor.post_process_object_detection(
        outputs, 
        threshold=0.3, 
        target_sizes=target_sizes
    )[0]
    
    boxes = results["boxes"].cpu().numpy().tolist()
    scores = results["scores"].cpu().numpy().tolist()
    
    # 4. Generate Answer
    count = len(scores)
    nl_answer = f"Found {count} instances of '{query_prompt}' in the image."
    
    # VRAM SAVING HACK
    del model
    del processor
    torch.cuda.empty_cache()
    
    return {"count": count, "boxes": boxes, "scores": scores, "description": nl_answer}


def tool_answer_vqa(img_path, question):
    """
    Tool for the LLM Agent to ask natural language questions about a single satellite image.
    Loads the 8-bit BLIP-2 model, gets the answer, and clears VRAM.
    """
    print(f"[Agent Tool] Asking VLM: '{question}'")
    from transformers import AutoProcessor, Blip2ForConditionalGeneration
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Load 8-bit Model safely if CUDA available, else standard precision
    if torch.cuda.is_available():
        from transformers import BitsAndBytesConfig
        quant_config = BitsAndBytesConfig(load_in_8bit=True)
        processor = AutoProcessor.from_pretrained("Salesforce/blip2-opt-2.7b")
        model = Blip2ForConditionalGeneration.from_pretrained(
            "Salesforce/blip2-opt-2.7b", 
            quantization_config=quant_config, 
            device_map="auto"
        )
    else:
        processor = AutoProcessor.from_pretrained("Salesforce/blip2-opt-2.7b")
        model = Blip2ForConditionalGeneration.from_pretrained(
            "Salesforce/blip2-opt-2.7b"
        ).to(device)
    
    # Process Image and Question
    image = Image.open(img_path).convert('RGB')
    prompt = f"Question: {question} Answer:"
    
    inputs = processor(images=image, text=prompt, return_tensors="pt").to(model.device)
    if torch.cuda.is_available():
        inputs["pixel_values"] = inputs["pixel_values"].to(torch.float16)
    
    # Inference
    generated_ids = model.generate(**inputs, max_new_tokens=30)
    answer = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
    
    if "Answer:" in answer:
        answer = answer.split("Answer:")[-1].strip()

    # VRAM SAVING HACK
    del model
    del processor
    torch.cuda.empty_cache()
    
    return answer
