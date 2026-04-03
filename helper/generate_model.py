import torch
import torchvision.models as models

print("Downloading official Vision Transformer (ViT-B/16) model...")
vit_model = models.vit_b_16()

file_name = "vit_base_production.pth"
torch.save(vit_model, file_name)

print(f"Done! Saved as {file_name} (approx. 346 MB)")