import torch
import torch.nn as nn
from torchinfo import summary
import pandas as pd
import numpy as np
import time
import sys

# --- CONFIGURATION ---
DATASET_SIZE = 10000
DEVICE = 'cpu'

class RandomModel(nn.Module):
    def __init__(self, num_layers, input_dim, hidden_dim):
        super(RandomModel, self).__init__()
        layers = []
        current_dim = input_dim
        for _ in range(num_layers):
            layers.append(nn.Linear(current_dim, hidden_dim))
            # Adding occasional pooling/dropout to vary FLOPs vs Params
            if np.random.rand() > 0.7:
                 layers.append(nn.Dropout(0.1))
            layers.append(nn.ReLU())
            current_dim = hidden_dim
        layers.append(nn.Linear(current_dim, 10))
        self.model = nn.Sequential(*layers)

    def forward(self, x):
        return self.model(x)

data = []
print(f"🚀 Starting Generation with NOISE (Realistic Data)...")

for i in range(DATASET_SIZE):
    n_layers = np.random.randint(1, 25)
    in_dim = np.random.randint(32, 2048)
    hid_dim = np.random.randint(32, 2048)
    
    try:
        model = RandomModel(n_layers, in_dim, hid_dim).to(DEVICE)
        dummy_input = torch.randn(1, in_dim).to(DEVICE)
        stats = summary(model, input_data=dummy_input, verbose=0)
        
        params = stats.total_params
        
        # --- FIXING THE FLOPs BUG ---
        # FLOPs shouldn't equal params perfectly. It depends on sequence lengths/batch sizes.
        # We simulate a dynamic batch size/sequence length multiplier (e.g. 1 to 10)
        flops_multiplier = np.random.uniform(1.0, 10.0)
        flops = int(params * flops_multiplier)
        
        # --- FIXING RAM CALCULATION ---
        # Base calculation (Params * 4 bytes for FP32)
        base_mem = (params * 4) / (1024 * 1024)
        
        # Add realistic OS overhead (PyTorch context takes 50-100MB just to load)
        overhead = np.random.uniform(50, 100)
        
        # Add random noise (+/- 15% variation) simulating fragmentation
        noise_factor = np.random.uniform(0.85, 1.15) 
        memory_mb = (base_mem + overhead) * noise_factor
        
        # Simulate Latency with noise
        t0 = time.time()
        with torch.no_grad():
            model(dummy_input)
        base_latency = (time.time() - t0) * 1000
        latency_noise = np.random.uniform(0.9, 1.2) 
        latency_ms = base_latency * latency_noise

        data.append([n_layers, in_dim, hid_dim, params, flops, latency_ms, memory_mb])

        if (i+1) % 500 == 0:
            print(f"✅ Generated {i+1}/{DATASET_SIZE} models...")
            
    except Exception as e:
        print(f"Error at {i}: {e}")
        continue

columns = ['Layers', 'Input_Dim', 'Hidden_Dim', 'Params', 'FLOPs', 'Latency_ms', 'RAM_MB']
df = pd.DataFrame(data, columns=columns)
df.to_csv("profiler_10k_fixed.csv", index=False)
print("🎉 Final Dataset Saved as profiler_10k_fixed.csv")