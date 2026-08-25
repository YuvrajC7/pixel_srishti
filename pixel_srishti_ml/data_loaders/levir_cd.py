import os
import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

class LevirCDDataset(Dataset):
    """
    Dataset for LEVIR-CD (Bi-temporal Change Detection).
    Expects structure:
    root_dir/
        A/ (Image T1)
        B/ (Image T2)
        label/ (Change Mask)
    """
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        
        self.dir_A = os.path.join(root_dir, 'A')
        self.dir_B = os.path.join(root_dir, 'B')
        self.dir_label = os.path.join(root_dir, 'label')
        
        # Verify directories exist
        if not all(os.path.exists(d) for d in [self.dir_A, self.dir_B, self.dir_label]):
            raise FileNotFoundError(f"Ensure A, B, and label directories exist in {root_dir}")
            
        self.image_files = sorted([f for f in os.listdir(self.dir_A) if f.endswith(('.png', '.jpg', '.tif'))])

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):
        img_name = self.image_files[idx]
        
        img_A_path = os.path.join(self.dir_A, img_name)
        img_B_path = os.path.join(self.dir_B, img_name)
        label_path = os.path.join(self.dir_label, img_name)
        
        # Load images (RGB) and mask (Grayscale)
        image_A = cv2.cvtColor(cv2.imread(img_A_path), cv2.COLOR_BGR2RGB)
        image_B = cv2.cvtColor(cv2.imread(img_B_path), cv2.COLOR_BGR2RGB)
        
        # Masks in LEVIR are usually 0 and 255. Convert to 0 and 1.
        mask = cv2.imread(label_path, cv2.IMREAD_GRAYSCALE)
        mask = (mask > 127).astype(np.float32)

        if self.transform:
            # Albumentations expects 'image' and 'image0' for dual image transforms
            augmented = self.transform(image=image_A, image0=image_B, mask=mask)
            image_A = augmented['image']
            image_B = augmented['image0']
            mask = augmented['mask']
            
        # Ensure channel-first format (C, H, W) for PyTorch if not converted by transform
        if not isinstance(image_A, torch.Tensor):
            image_A = torch.from_numpy(image_A.transpose(2, 0, 1)).float() / 255.0
            image_B = torch.from_numpy(image_B.transpose(2, 0, 1)).float() / 255.0
            mask = torch.from_numpy(mask).unsqueeze(0).float()
            
        return image_A, image_B, mask
