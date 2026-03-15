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

# LSTM now accepts input_size=3 (CPU, Hour, Min)
class SimpleLSTM(nn.Module):
    def __init__(self, input_dim=3):
        super(SimpleLSTM, self).__init__()
        self.lstm = nn.LSTM(input_dim, 64, num_layers=1, batch_first=True)
        self.dropout = nn.Dropout(0.2)
        self.fc = nn.Linear(64, 1)
        
    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :]) 
        return self.fc(out)

# --- 2. THE SYSTEM BRAIN ---
class SmartScaleSystem:
    def __init__(self):
        print("Initializing SmartScale Backend...")
        
        # Path setup
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        self.models_dir = os.path.join(project_root, "models")
        
        self.load_profiler()
        self.load_optimizer()
        print("System Core Ready.")

    def load_profiler(self):
        try:
            self.profiler_model = ProfilerNN().to(DEVICE)
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
                print(f"    Warning: {path_model} not found.")
        except Exception as e:
            print(f"    Failed to load Profiler: {e}")

    def load_optimizer(self):
        """Loads the NEW LSTM model and BOTH scalers"""
        try:
            path_model = os.path.join(self.models_dir, 'resource_optimizer.pth')
            path_scaler = os.path.join(self.models_dir, 'traffic_scaler.pkl')
            path_time_scaler = os.path.join(self.models_dir, 'time_scaler.pkl')

            if os.path.exists(path_model):
                # Initialize with input_dim=3
                self.optimizer_model = SimpleLSTM(input_dim=3).to(DEVICE)
                self.optimizer_model.load_state_dict(torch.load(path_model, map_location=DEVICE))
                self.optimizer_model.eval()
                
                self.traffic_scaler = joblib.load(path_scaler)
                self.time_scaler = joblib.load(path_time_scaler) 
                print("    Module 2: Resource Optimizer (Time-Aware LSTM) - ACTIVE")
            else:
                print(f"    Warning: {path_model} not found.")
        except Exception as e:
            print(f"    Failed to load Optimizer: {e}")

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

    def predict_next_load(self, history_list, current_minute_index):
        """Used by the Simulator with minute indexes."""
        return self._execute_prediction(history_list, current_minute_index)

    def predict_live_load(self, history_list, current_time_dt):
        """Used by the Live AWS Dashboard with real datetime objects."""
        # Convert datetime to a pseudo-index for the logic
        minute_index = current_time_dt.hour * 60 + current_time_dt.minute
        return self._execute_prediction(history_list, minute_index)

    def _execute_prediction(self, history_list, minute_index):
        """Internal helper to process the 12-step (60 min) sequence."""
        if not hasattr(self, 'optimizer_model'): return 0.0
        
        # Prepare 12 steps (one every 5 mins)
        if len(history_list) < 60:
            padding = [history_list[-1]] * (60 - len(history_list)) if history_list else [0]*60
            history_list = padding + history_list
        
        resampled_history = history_list[-60:][::5] 
        time_features = []
        traffic_features = []
        
        for i, cpu_val in enumerate(resampled_history):
            step_time = minute_index - ((11-i) * 5)
            hour = (step_time // 60) % 24
            min_of_hour = step_time % 60
            time_features.append([hour, min_of_hour])
            traffic_features.append([cpu_val])

        # Scaling & Prediction
        traffic_scaled = self.traffic_scaler.transform(np.log1p(np.array(traffic_features)))
        time_scaled = self.time_scaler.transform(np.array(time_features))
        combined_data = np.hstack([traffic_scaled, time_scaled])
        
        input_tensor = torch.tensor(combined_data, dtype=torch.float32).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            pred_scaled = self.optimizer_model(input_tensor).cpu().numpy()
            
        pred_real = np.expm1(self.traffic_scaler.inverse_transform(pred_scaled)[0][0])
        return max(0.0, float(pred_real))