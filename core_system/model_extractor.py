# import torch
# import os

# def extract_features_from_pth(file_path):
#     """
#     Automatically reads a PyTorch .pth file and extracts structural math.
#     Handles both state_dicts (recommended) and full model saves.
#     """
#     try:
#         # Load the model directly into CPU RAM to avoid GPU errors
#         model_data = torch.load(file_path, map_location='cpu', weights_only=False)
        
#         # Check if it's a state_dict (dictionary of weights) or a full model class
#         if isinstance(model_data, dict):
#             # 1. Count Parameters (in Millions)
#             total_params = sum(t.numel() for t in model_data.values()) / 1_000_000
#             # 2. Count Layers (Keys in the dictionary)
#             layers = len(model_data.keys())
#         else:
#             # It's a full model object
#             total_params = sum(p.numel() for p in model_data.parameters()) / 1_000_000
#             layers = len(list(model_data.modules()))
        
#         # Since exact FLOPs require dummy data and the original class definition,
#         # we use an industry-standard heuristic approximation for this prototype.
#         estimated_flops = total_params * 0.15  
#         estimated_hidden_dim = 512 
        
#         return total_params, estimated_flops, layers, estimated_hidden_dim

#     except Exception as e:
#         raise Exception(f"Failed to read .pth file: {e}")



import torch
from collections import OrderedDict

def extract_features_from_pth(file_path):
    """
    Automatically reads a PyTorch .pth file and extracts structural math.
    Bulletproofed to handle both state_dicts (OrderedDict) and full models.
    """
    try:
        # Load the model directly into CPU RAM to avoid GPU errors
        model_data = torch.load(file_path, map_location='cpu', weights_only=False)
        
        total_params = 0
        layers = 0
        
        # Check if it's a state_dict (Dictionary of weights)
        if isinstance(model_data, dict) or isinstance(model_data, OrderedDict):
            # Safely count parameters only if the item is a tensor
            for key, value in model_data.items():
                if hasattr(value, 'numel'):
                    total_params += value.numel()
            layers = len(model_data.keys())
            
        # Otherwise, it's a full model class object
        else:
            total_params = sum(p.numel() for p in model_data.parameters())
            layers = len(list(model_data.modules()))
            
        # Convert parameters to Millions for the ProfilerNN
        total_params_millions = total_params / 1_000_000
        
        # Since exact FLOPs require dummy data and the original class definition,
        # we use an industry-standard heuristic approximation for this prototype.
        estimated_flops = total_params_millions * 0.15  
        estimated_hidden_dim = 512 
        
        return total_params_millions, estimated_flops, layers, estimated_hidden_dim

    except Exception as e:
        raise Exception(f"{e}")