import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm import tqdm
import sys

# Ensure the parent directory is in path when running on cloud notebooks
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datasets.levir_cd import LevirCDDataset
from models.siamese_unet import SiameseUNet
from tools.agent_tools import generate_change_description

def train_change_detection(data_dir, batch_size=8, epochs=10, checkpoint_dir='./checkpoints'):
    """
    Phase 2: Training the Flagship Siamese U-Net.
    Includes frequent checkpointing for cloud session timeouts and 
    qualitative validation with the NL generator.
    """
    os.makedirs(checkpoint_dir, exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training on device: {device}")
    
    # 1. Dataset & DataLoader (Fallback to train dir if val doesn't exist for quick tests)
    train_dir = os.path.join(data_dir, 'train')
    val_dir = os.path.join(data_dir, 'val') if os.path.exists(os.path.join(data_dir, 'val')) else train_dir
    
    train_dataset = LevirCDDataset(root_dir=train_dir)
    val_dataset = LevirCDDataset(root_dir=val_dir)
    
    # num_workers=2 is safe for free Colab/Kaggle instances
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=1, shuffle=False)
    
    # 2. Model, Loss, Optimizer
    model = SiameseUNet().to(device)
    # BCEWithLogitsLoss combines Sigmoid and BCELoss for numerical stability
    criterion = nn.BCEWithLogitsLoss() 
    optimizer = optim.AdamW(model.parameters(), lr=1e-4)
    
    # --- GRACEFUL DEGRADATION / SESSION TIMEOUT PROTECTION ---
    start_epoch = 0
    latest_ckpt = os.path.join(checkpoint_dir, 'latest_cd_model.pth')
    if os.path.exists(latest_ckpt):
        print(f"Recovering from session timeout. Loading checkpoint: {latest_ckpt}")
        checkpoint = torch.load(latest_ckpt, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        print(f"Resuming from Epoch {start_epoch + 1}")

    # 3. Training Loop
    for epoch in range(start_epoch, epochs):
        model.train()
        epoch_loss = 0
        
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}")
        for img_A, img_B, mask in pbar:
            img_A, img_B, mask = img_A.to(device), img_B.to(device), mask.to(device)
            
            optimizer.zero_grad()
            outputs = model(img_A, img_B)
            
            loss = criterion(outputs, mask)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            pbar.set_postfix({'loss': loss.item()})
        
        # Save Checkpoint explicitly at the end of every epoch
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': epoch_loss,
        }, latest_ckpt)
        
        # 4. Qualitative Validation & NL Template Check
        model.eval()
        with torch.no_grad():
            # Grab just one sample to validate
            val_A, val_B, val_mask = next(iter(val_loader))
            val_A, val_B = val_A.to(device), val_B.to(device)
            
            val_pred = model(val_A, val_B)
            # Threshold the raw logits into a binary mask
            val_pred_binary = (torch.sigmoid(val_pred) > 0.5).cpu().numpy().squeeze()
            
            # Wire in the templated language-generation step
            nl_desc = generate_change_description(val_pred_binary)
            print(f"\n[Validation] Generated NL Output: {nl_desc}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train Siamese U-Net for Change Detection")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to LEVIR-CD or OSCD dataset")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size (keep low for T4 GPU)")
    args = parser.parse_args()
    
    train_change_detection(data_dir=args.data_dir, epochs=args.epochs, batch_size=args.batch_size)
