import os
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

class LandCoverDataset(Dataset):
    """
    Dataset for LandCover.ai or DeepGlobe Land Cover (Semantic Segmentation).
    Expects structure:
    root_dir/
        images/
        masks/
    """
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        
        self.dir_images = os.path.join(root_dir, 'images')
        self.dir_masks = os.path.join(root_dir, 'masks')
        
        if not all(os.path.exists(d) for d in [self.dir_images, self.dir_masks]):
            raise FileNotFoundError(f"Ensure images and masks directories exist in {root_dir}")
            
        self.image_files = sorted([f for f in os.listdir(self.dir_images) if f.endswith(('.png', '.jpg', '.tif'))])

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):
        img_name = self.image_files[idx]
        
        # Mask might have a different extension depending on the dataset preprocessing,
        # adjust this logic if masks are e.g., _mask.png
        mask_name = img_name.replace('.jpg', '.png') if img_name.endswith('.jpg') else img_name
        
        img_path = os.path.join(self.dir_images, img_name)
        mask_path = os.path.join(self.dir_masks, mask_name)
        
        image = cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2RGB)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        
        if self.transform:
            augmented = self.transform(image=image, mask=mask)
            image = augmented['image']
            mask = augmented['mask']
            
        # Ensure channel-first format (C, H, W) for PyTorch if not converted by transform
        if not isinstance(image, torch.Tensor):
            image = torch.from_numpy(image.transpose(2, 0, 1)).float() / 255.0
            mask = torch.from_numpy(mask).long() # Use long for categorical cross-entropy
            
        return image, mask
