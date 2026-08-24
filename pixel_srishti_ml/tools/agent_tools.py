import os
import torch
import numpy as np
from PIL import Image
import torchvision.transforms as T

# Import your successfully trained flagship model
from models.siamese_unet import SiameseUNet

def generate_change_description(mask_array):
    """Helper to convert a binary mask array into a plain English sentence."""
    total_pixels = mask_array.size
    changed_pixels = np.sum(mask_array > 0)
    change_ratio = (changed_pixels / total_pixels) * 100
    
    if change_ratio < 1.0:
        return f"No significant changes detected in the specified area (change was only {change_ratio:.2f}%)."
    elif change_ratio < 10.0:
        return f"Minor changes detected, covering {change_ratio:.2f}% of the region. This may indicate initial watershed development works."
    else:
        return f"Major changes detected! {change_ratio:.2f}% of the region has been altered, indicating significant construction or water accumulation."

def tool_detect_change(img_A_path, img_B_path, checkpoint_path="checkpoints/latest_cd_model.pth"):
    """
    Tool for the LLM Agent to detect structural changes between two dates.
    Loads the Siamese U-Net, runs inference, saves the visual mask, and clears VRAM.
    
    Returns:
        nl_answer (str): Plain English text describing the change.
        output_mask_path (str): Filepath to the generated mask image for the UI to display.
    """
    print("[Agent Tool] Running Change Detection...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 1. Load Model
    model = SiameseUNet().to(device)
    if os.path.exists(checkpoint_path):
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
    else:
        print("[Warning] No checkpoint found! Did you copy the checkpoint from Kaggle?")
    
    model.eval()

    # 2. Prepare Images
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
        mask = (torch.sigmoid(output) > 0.5).cpu().numpy().squeeze()

    # 4. Generate Text Answer for the Agent
    nl_answer = generate_change_description(mask)

    # 5. Save the visual mask for the Frontend UI
    mask_img = Image.fromarray((mask * 255).astype(np.uint8))
    mask_img = mask_img.resize(orig_size, Image.NEAREST)
    output_mask_path = "frontend_output_mask.png"
    mask_img.save(output_mask_path)

    # 6. VRAM SAVING HACK: Delete model and clear GPU memory so LangGraph doesn't crash
    del model
    torch.cuda.empty_cache()

    return nl_answer, output_mask_path


def tool_answer_vqa(img_path, question):
    """
    Tool for the LLM Agent to ask natural language questions about a single satellite image.
    Loads the 8-bit BLIP-2 model, gets the answer, and clears VRAM.
    
    Returns:
        answer (str): The VLM's text response.
    """
    print(f"[Agent Tool] Asking VLM: '{question}'")
    from transformers import AutoProcessor, Blip2ForConditionalGeneration, BitsAndBytesConfig
    
    # 1. Load 8-bit Model safely
    quant_config = BitsAndBytesConfig(load_in_8bit=True)
    processor = AutoProcessor.from_pretrained("Salesforce/blip2-opt-2.7b")
    model = Blip2ForConditionalGeneration.from_pretrained(
        "Salesforce/blip2-opt-2.7b", 
        quantization_config=quant_config, 
        device_map="auto"
    )
    
    # 2. Process Image and Question
    image = Image.open(img_path).convert('RGB')
    prompt = f"Question: {question} Answer:"
    
    inputs = processor(images=image, text=prompt, return_tensors="pt").to(model.device)
    inputs["pixel_values"] = inputs["pixel_values"].to(torch.float16)
    
    # 3. Inference
    generated_ids = model.generate(**inputs, max_new_tokens=30)
    answer = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
    
    # Clean up the weird prompt echoing
    if "Answer:" in answer:
        answer = answer.split("Answer:")[-1].strip()

    # 4. VRAM SAVING HACK: Delete model and clear GPU memory
    del model
    del processor
    torch.cuda.empty_cache()
    
    return answer
