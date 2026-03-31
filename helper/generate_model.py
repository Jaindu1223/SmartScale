# import torch
# import torchvision.models as models

# print("Downloading official VGG-16 model (this might take a minute)...")
# vgg16_model = models.vgg16()
# torch.save(vgg16_model, "vgg16_production.pth")
# print("✅ Done! Saved as vgg16_production.pth (approx. 528 MB)")

import torch
import torchvision.models as models

print("Downloading official Vision Transformer (ViT-B/16) model...")
# This is much lighter than VGG-16 but still heavy enough to test your limits!
vit_model = models.vit_b_16()

file_name = "vit_base_production.pth"
torch.save(vit_model, file_name)

print(f"✅ Done! Saved as {file_name} (approx. 346 MB)")