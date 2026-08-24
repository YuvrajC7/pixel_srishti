import torch
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

class GroundingDINOWrapper:
    """
    Zero-shot inference wrapper for Grounding DINO.
    Priority: Low effort, use as-is. DO NOT fine-tune.
    """
    def __init__(self, model_id="IDEA-Research/grounding-dino-base", device=None):
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Loading Grounding DINO on {self.device}...")
        
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id).to(self.device)
        self.model.eval()

    @torch.no_grad()
    def infer(self, image, prompt, box_threshold=0.3, text_threshold=0.25):
        """
        image: PIL Image
        prompt: natural language query, e.g. "water body. vegetation patch. bare soil."
        """
        # Format text input (DINO expects lowercase, dot-separated phrases)
        prompt = prompt.lower()
        if not prompt.endswith("."):
            prompt += "."

        inputs = self.processor(images=image, text=prompt, return_tensors="pt").to(self.device)
        
        outputs = self.model(**inputs)
        
        # Convert outputs (bounding boxes and logits) to standard format based on image size
        target_sizes = torch.tensor([image.size[::-1]])
        results = self.processor.image_processor.post_process_object_detection(
            outputs, 
            threshold=box_threshold, 
            target_sizes=target_sizes
        )[0]
        
        # Extract confident predictions
        boxes = results["boxes"].cpu().numpy().tolist()
        scores = results["scores"].cpu().numpy().tolist()
        labels = results["labels"] # These are integer indices mapping to the text prompt tokens
        
        return {
            "boxes": boxes,
            "scores": scores,
            "raw_labels": labels
        }
