import torch
from collections import OrderedDict

def extract_features_from_pth(file_path):
    """
    Automatically reads a PyTorch .pth file and extracts structural math.
    Returns the exact 5 features required by the upgraded SmartScale Profiler.
    """
    try:
        # Load the model directly into CPU RAM
        model_data = torch.load(file_path, map_location='cpu', weights_only=False)
        
        total_params = 0
        layers = 0
        
        # Check if it's a state_dict
        if isinstance(model_data, dict) or isinstance(model_data, OrderedDict):
            for key, value in model_data.items():
                if hasattr(value, 'numel'):
                    total_params += value.numel()
            layers = len(model_data.keys())
        # Otherwise, full model object
        else:
            total_params = sum(p.numel() for p in model_data.parameters())
            layers = len(list(model_data.modules()))
            
        # --- HEURISTICS FOR MISSING METADATA ---
        # Since we are reading a raw .pth without the class definition, 
        # we estimate the dimensions and FLOPs to feed the AI.
        input_dim = 256
        hidden_dim = 512 
        estimated_flops = total_params * 2.5  
        
        # Return exactly 5 features
        return layers, input_dim, hidden_dim, total_params, estimated_flops

    except Exception as e:
        raise Exception(f"Extraction Error: {e}")