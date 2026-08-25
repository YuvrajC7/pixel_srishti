import os
import json
from PIL import Image
import torch
from torch.utils.data import Dataset

class RSVQA_Dataset(Dataset):
    """
    Dataset loader for RSVQA.
    Expects a JSON file mapping questions to images and answers.
    Format of JSON:
    [
        {"img_id": "123", "question": "Are there water bodies?", "answers": ["yes"]},
        ...
    ]
    """
    def __init__(self, images_dir, annotations_file, transform=None):
        self.images_dir = images_dir
        self.transform = transform
        
        with open(annotations_file, 'r') as f:
            self.annotations = json.load(f)

    def __len__(self):
        return len(self.annotations)

    def __getitem__(self, idx):
        item = self.annotations[idx]
        img_id = item['img_id']
        question = item['question']
        
        # Taking the first answer or majority answer depending on RSVQA version formatting
        answer = item['answers'][0] if isinstance(item['answers'], list) else item['answers']
        
        # RSVQA images are often stored directly with their ID as filename
        # Modify the extension if needed (.tif or .png)
        img_path = os.path.join(self.images_dir, f"{img_id}.png")
        if not os.path.exists(img_path):
            img_path = os.path.join(self.images_dir, f"{img_id}.tif")
            
        try:
            image = Image.open(img_path).convert('RGB')
        except FileNotFoundError:
            raise FileNotFoundError(f"Image {img_path} not found.")

        # For VLM pipelines (like HuggingFace processors), returning PIL images
        # is often easier than tensors because the Processor handles resizing/normalization.
        if self.transform:
            image = self.transform(image)
            
        return {
            'image': image,
            'question': question,
            'answer': answer,
            'img_id': img_id
        }
