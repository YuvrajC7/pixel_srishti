import torch
import torch.nn as nn
import segmentation_models_pytorch as smp

class SiameseUNet(nn.Module):
    """
    Bi-temporal Change Detection: Twin shared-weight encoders, feature-difference decoder.
    Built efficiently using SMP's battle-tested blocks.
    """
    def __init__(self, encoder_name='resnet18', encoder_weights='imagenet'):
        super().__init__()
        # Shared Encoder (Weights are identical for Image A and Image B)
        self.encoder = smp.encoders.get_encoder(
            encoder_name, 
            in_channels=3, 
            depth=5, 
            weights=encoder_weights
        )
        
        # Standard U-Net Decoder
        self.decoder = smp.decoders.unet.decoder.UnetDecoder(
            encoder_channels=self.encoder.out_channels,
            decoder_channels=(256, 128, 64, 32, 16),
            n_blocks=5,
            use_batchnorm=True,
            center=False,
            attention_type=None
        )
        
        # Output layer for binary change mask (1 class)
        self.segmentation_head = smp.base.SegmentationHead(
            in_channels=16, 
            out_channels=1, 
            activation=None, 
            kernel_size=3
        )

    def forward(self, x1, x2):
        # 1. Extract features from both images using the shared encoder
        features1 = self.encoder(x1)
        features2 = self.encoder(x2)
        
        # 2. Compute absolute feature difference at every spatial level
        diff_features = [torch.abs(f1 - f2) for f1, f2 in zip(features1, features2)]
        
        # 3. Decode the difference features to get the change mask
        decoder_output = self.decoder(*diff_features)
        masks = self.segmentation_head(decoder_output)
        
        return masks
