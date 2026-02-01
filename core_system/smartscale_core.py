# import torch
# import torch.nn as nn
# import numpy as np
# import joblib
# import os
# import pandas as pd

# # --- CONFIGURATION ---
# DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# # --- 1. MODEL ARCHITECTURES ---

# # A. Architecture Profiler (Neural Network for RAM Prediction)
# # This must match the architecture used in your '2_train_profiler.py'
# class ProfilerNN(nn.Module):
#     def __init__(self):
#         super(ProfilerNN, self).__init__()
#         self.net = nn.Sequential(
#             nn.Linear(4, 64),
#             nn.ReLU(),
#             nn.Dropout(0.2),
#             nn.Linear(64, 32),
#             nn.ReLU(),
#             nn.Linear(32, 1)
#         )
        
#     def forward(self, x):
#         return self.net(x)

# # B. Resource Optimizer (Bi-Directional LSTM for Traffic)
# class GoogleOptimizer(nn.Module):
#     def __init__(self):
#         super(GoogleOptimizer, self).__init__()
#         self.lstm = nn.LSTM(input_size=1, hidden_size=64, num_layers=2, batch_first=True, bidirectional=True, dropout=0.2)
#         self.fc = nn.Linear(64 * 2, 1) 
        
#     def forward(self, x):
#         out, _ = self.lstm(x)
#         out = out[:, -1, :] 
#         return self.fc(out)

# # --- 2. THE SYSTEM BRAIN ---

# class SmartScaleSystem:
#     def __init__(self):
#         print("🧠 Initializing SmartScale Backend...")
#         self.load_profiler()
#         self.load_optimizer()
#         print("✅ System Core Ready.")

#     def load_profiler(self):
#         """Loads the PyTorch Profiler (.pth) and its Scalers (.pkl)"""
#         try:
#             # 1. Initialize the Model Structure
#             self.profiler_model = ProfilerNN().to(DEVICE)
            
#             # 2. Load Weights
#             if os.path.exists('../models/profiler_nn_model.pth'):
#                 self.profiler_model.load_state_dict(torch.load('../models/profiler_nn_model.pth', map_location=DEVICE))
#                 self.profiler_model.eval()
                
#                 # 3. Load Scalers
#                 self.prof_scaler_x = joblib.load('../models/profiler_scaler_x.pkl')
#                 self.prof_scaler_y = joblib.load('../models/profiler_scaler_y.pkl')
                
#                 print("   🔹 Module 1: Architecture Profiler (Neural Net) - ACTIVE")
#             else:
#                 print("   ⚠️ Warning: 'profiler_nn_model.pth' not found.")
                
#         except Exception as e:
#             print(f"   ❌ Failed to load Profiler: {e}")

#     def load_optimizer(self):
#         """Loads the Resource Optimizer (.pth) and its Scaler (.pkl)"""
#         try:
#             if os.path.exists('../models/resource_optimizer.pth'):
#                 self.optimizer_model = GoogleOptimizer().to(DEVICE)
#                 self.optimizer_model.load_state_dict(torch.load('../models/resource_optimizer.pth', map_location=DEVICE))
#                 self.optimizer_model.eval()
                
#                 self.traffic_scaler = joblib.load('../models/traffic_scaler.pkl')
#                 print("   🔹 Module 2: Resource Optimizer (LSTM) - ACTIVE")
#             else:
#                 print("   ⚠️ Warning: 'resource_optimizer.pth' not found.")
#         except Exception as e:
#             print(f"   ❌ Failed to load Optimizer: {e}")

#     # --- PUBLIC API FUNCTIONS ---

#     def profile_model(self, params, flops, layers, hidden_dim):
#         """
#         Step 1: Predict RAM for a new uploaded model using Neural Net.
#         Input: Model metadata [Params, FLOPs, Layers, Hidden_Dim]
#         Output: Recommended RAM (MB)
#         """
#         if not hasattr(self, 'profiler_model'): return 512 # Fallback

#         # 1. Prepare Input Array
#         input_data = np.array([[params, flops, layers, hidden_dim]])
        
#         # 2. Scale Input (Using scaler_x)
#         input_scaled = self.prof_scaler_x.transform(input_data)
#         input_tensor = torch.FloatTensor(input_scaled).to(DEVICE)
        
#         # 3. Predict (Neural Net)
#         with torch.no_grad():
#             prediction_scaled = self.profiler_model(input_tensor).cpu().numpy()
            
#         # 4. Inverse Scale Output (Using scaler_y to get real MB)
#         predicted_mb = self.prof_scaler_y.inverse_transform(prediction_scaled)[0][0]
        
#         return max(128, round(predicted_mb, 2)) # Safety floor

#     def predict_next_load(self, history_list):
#         """
#         Step 2: Predict Traffic Spikes using LSTM.
#         Input: List of last 120 minutes of CPU load
#         Output: Predicted CPU load for next minute
#         """
#         if not hasattr(self, 'optimizer_model'): return 0.0

#         # Handle missing history padding
#         if len(history_list) < 120:
#             padding = [history_list[-1]] * (120 - len(history_list)) if history_list else [0]*120
#             history_list = padding + history_list
        
#         # Take strictly the last 120 points
#         recent_history = history_list[-120:]

#         # Log Transform & Scale
#         history_log = np.log1p(np.array(recent_history).reshape(-1, 1))
#         history_scaled = self.traffic_scaler.transform(history_log)
        
#         # Reshape for LSTM
#         input_tensor = torch.tensor(history_scaled, dtype=torch.float32).unsqueeze(0).to(DEVICE)
        
#         # Predict
#         with torch.no_grad():
#             pred_scaled = self.optimizer_model(input_tensor).cpu().numpy()
            
#         # Inverse Transform
#         pred_log = self.traffic_scaler.inverse_transform(pred_scaled)
#         pred_real = np.expm1(pred_log)[0][0]
        
#         return max(0.0, float(pred_real))

# # --- TEST RUNNER ---
# if __name__ == "__main__":
#     system = SmartScaleSystem()
    
#     print("\n--- TEST 1: Cold Start Profiling (Neural Net) ---")
#     # Simulate BERT Model Upload
#     ram = system.profile_model(params=110_000_000, flops=15_000_000_000, layers=12, hidden_dim=768)
#     print(f"Model: BERT-Base | Recommended RAM: {ram} MB")
    
#     print("\n--- TEST 2: Proactive Scaling (LSTM) ---")
#     # Simulate 2 hours of fake traffic
#     fake_history = [0.5] * 120 
#     load = system.predict_next_load(fake_history)
#     print(f"Current Load: 0.5 | Predicted Next Min: {load:.4f}")



import torch
import torch.nn as nn
import numpy as np
import joblib
import os
import pandas as pd

# --- CONFIGURATION ---
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# --- 1. MODEL ARCHITECTURES ---
class ProfilerNN(nn.Module):
    def __init__(self):
        super(ProfilerNN, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(4, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    def forward(self, x): return self.net(x)

class GoogleOptimizer(nn.Module):
    def __init__(self):
        super(GoogleOptimizer, self).__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=64, num_layers=2, batch_first=True, bidirectional=True, dropout=0.2)
        self.fc = nn.Linear(64 * 2, 1) 
    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :] 
        return self.fc(out)

# --- 2. THE SYSTEM BRAIN ---
class SmartScaleSystem:
    def __init__(self):
        print("🧠 Initializing SmartScale Backend...")
        
        # FIX: Dynamically find the project root to locate models
        current_dir = os.path.dirname(os.path.abspath(__file__)) # .../SmartScale/core_system
        project_root = os.path.dirname(current_dir)              # .../SmartScale
        self.models_dir = os.path.join(project_root, "models")
        
        self.load_profiler()
        self.load_optimizer()
        print("✅ System Core Ready.")

    def load_profiler(self):
        try:
            self.profiler_model = ProfilerNN().to(DEVICE)
            # Use dynamic paths
            path_model = os.path.join(self.models_dir, 'profiler_nn_model.pth')
            path_sx = os.path.join(self.models_dir, 'profiler_scaler_x.pkl')
            path_sy = os.path.join(self.models_dir, 'profiler_scaler_y.pkl')

            if os.path.exists(path_model):
                self.profiler_model.load_state_dict(torch.load(path_model, map_location=DEVICE))
                self.profiler_model.eval()
                self.prof_scaler_x = joblib.load(path_sx)
                self.prof_scaler_y = joblib.load(path_sy)
                print("   🔹 Module 1: Architecture Profiler - ACTIVE")
            else:
                print(f"   ⚠️ Warning: {path_model} not found.")
        except Exception as e:
            print(f"   ❌ Failed to load Profiler: {e}")

    def load_optimizer(self):
        try:
            path_model = os.path.join(self.models_dir, 'resource_optimizer.pth')
            path_scaler = os.path.join(self.models_dir, 'traffic_scaler.pkl')

            if os.path.exists(path_model):
                self.optimizer_model = GoogleOptimizer().to(DEVICE)
                self.optimizer_model.load_state_dict(torch.load(path_model, map_location=DEVICE))
                self.optimizer_model.eval()
                self.traffic_scaler = joblib.load(path_scaler)
                print("   🔹 Module 2: Resource Optimizer - ACTIVE")
            else:
                print(f"   ⚠️ Warning: {path_model} not found.")
        except Exception as e:
            print(f"   ❌ Failed to load Optimizer: {e}")

    # --- API FUNCTIONS ---
    def profile_model(self, params, flops, layers, hidden_dim):
        if not hasattr(self, 'profiler_model'): return 512
        input_data = np.array([[params, flops, layers, hidden_dim]])
        input_scaled = self.prof_scaler_x.transform(input_data)
        input_tensor = torch.FloatTensor(input_scaled).to(DEVICE)
        with torch.no_grad():
            prediction_scaled = self.profiler_model(input_tensor).cpu().numpy()
        predicted_mb = self.prof_scaler_y.inverse_transform(prediction_scaled)[0][0]
        return max(128, round(predicted_mb, 2))

    def predict_next_load(self, history_list):
        if not hasattr(self, 'optimizer_model'): return 0.0
        if len(history_list) < 120:
            padding = [history_list[-1]] * (120 - len(history_list)) if history_list else [0]*120
            history_list = padding + history_list
        recent_history = history_list[-120:]
        history_log = np.log1p(np.array(recent_history).reshape(-1, 1))
        history_scaled = self.traffic_scaler.transform(history_log)
        input_tensor = torch.tensor(history_scaled, dtype=torch.float32).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            pred_scaled = self.optimizer_model(input_tensor).cpu().numpy()
        pred_log = self.traffic_scaler.inverse_transform(pred_scaled)
        pred_real = np.expm1(pred_log)[0][0]
        return max(0.0, float(pred_real))

if __name__ == "__main__":
    system = SmartScaleSystem()
    print("Test Complete.")