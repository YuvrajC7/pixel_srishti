import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import segmentation_models_pytorch as smp
from tqdm import tqdm
import sys

# Ensure parent directory is in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loaders.landcover import LandCoverDataset

def train_segmentation(data_dir, epochs=5, batch_size=4):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training on device: {device}")

    # LandCover.ai has 4 main classes: 0(Background), 1(Buildings), 2(Woodlands), 3(Water)
    # DeepLabV3+ Initialization
    print("Initializing DeepLabV3+ with ResNet34 backbone...")
    model = smp.DeepLabV3Plus(
        encoder_name="resnet34",
        encoder_weights="imagenet",
        in_channels=3,
        classes=4,
    ).to(device)

    # Dataset and DataLoader
    print(f"Loading dataset from: {data_dir}")
    dataset = LandCoverDataset(root_dir=data_dir, transform=None)
    
    # Keeping batch size small to avoid CUDA OOM (Out of Memory)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=2)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-4)

    os.makedirs('checkpoints', exist_ok=True)

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        loop = tqdm(dataloader, desc=f"Epoch {epoch+1}/{epochs}")
        
        for images, masks in loop:
            images = images.to(device)
            masks = masks.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            
            loss = criterion(outputs, masks)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            loop.set_postfix(loss=loss.item())

        print(f"Epoch {epoch+1} Avg Loss: {epoch_loss/len(dataloader):.4f}")
        
        # Save checkpoint after every epoch
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': epoch_loss/len(dataloader),
        }, 'checkpoints/latest_seg_model.pth')

    print("Training Complete! Saved to checkpoints/latest_seg_model.pth")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, required=True, help="Path to LandCover.ai dataset root")
    parser.add_argument('--epochs', type=int, default=5)
    parser.add_argument('--batch_size', type=int, default=4)
    args = parser.parse_args()
    
    train_segmentation(args.data_dir, args.epochs, args.batch_size)
