import torch
import torch.nn as nn
import numpy as np
import joblib
import os
import pandas as pd

# CONFIGURATION
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# MODEL ARCHITECTURES
class ProfilerNN(nn.Module):
    def __init__(self):
        super(ProfilerNN, self).__init__()
        # Matches 5-input, deep architecture
        self.net = nn.Sequential(
            nn.Linear(5, 128),      
            nn.BatchNorm1d(128),    
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    def forward(self, x): return self.net(x)

#  6 feature Proactive LSTM
class ProactiveLSTM(nn.Module):
    def __init__(self, input_dim=6):
        super(ProactiveLSTM, self).__init__()
        self.lstm = nn.LSTM(input_dim, 64, num_layers=1, batch_first=True)
        self.fc1 = nn.Linear(64, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, 1)
        
    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :] 
        out = self.relu(self.fc1(out))
        return self.fc2(out)

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
            path_model = os.path.join(self.models_dir, '1_architecture_profiler_model.pth')
            path_sx = os.path.join(self.models_dir, '1_architecture_profiler_scaler_x.pkl')
            path_sy = os.path.join(self.models_dir, '1_architecture_profiler_scaler_y.pkl')

            if os.path.exists(path_model):
                self.profiler_model.load_state_dict(torch.load(path_model, map_location=DEVICE))
                self.profiler_model.eval()
                self.prof_scaler_x = joblib.load(path_sx)
                self.prof_scaler_y = joblib.load(path_sy)
                print("   Module 1: Architecture Profiler - ACTIVE")
            else:
                print(f"    Warning: {path_model} not found.")
        except Exception as e:
            print(f"    Failed to load Profiler: {e}")

    def load_optimizer(self):
        """Loads the NEW 6-Feature Proactive LSTM model and BOTH scalers"""
        try:
            # UPDATED: Pointing to your new high-accuracy model files
            path_model = os.path.join(self.models_dir, '2_resource_optimizer.pth')
            path_scaler = os.path.join(self.models_dir, '2_traffic_scaler.pkl')
            path_time_scaler = os.path.join(self.models_dir, '2_time_scaler.pkl')

            if os.path.exists(path_model):
                # Initialize with input_dim=6
                self.optimizer_model = ProactiveLSTM(input_dim=6).to(DEVICE)
                self.optimizer_model.load_state_dict(torch.load(path_model, map_location=DEVICE))
                self.optimizer_model.eval()
                
                self.traffic_scaler = joblib.load(path_scaler)
                self.time_scaler = joblib.load(path_time_scaler) 
                print("   Module 2: Resource Optimizer (Proactive LSTM) - ACTIVE")
            else:
                print(f"    Warning: {path_model} not found.")
        except Exception as e:
            print(f"    Failed to load Optimizer: {e}")

    # --- API FUNCTIONS ---
    def profile_model(self, layers, input_dim, hidden_dim, params, flops):
        if not hasattr(self, 'profiler_model'): return 512
        
        # Creating the array in the exact order: ['Layers', 'Input_Dim', 'Hidden_Dim', 'Params', 'FLOPs']
        input_data = np.array([[layers, input_dim, hidden_dim, params, flops]])
        
        input_scaled = self.prof_scaler_x.transform(input_data)
        input_tensor = torch.FloatTensor(input_scaled).to(DEVICE)
        
        # Set to eval mode before predicting
        self.profiler_model.eval()
        with torch.no_grad():
            prediction_scaled = self.profiler_model(input_tensor).cpu().numpy()
            
        predicted_mb = self.prof_scaler_y.inverse_transform(prediction_scaled)[0][0]
        return max(128, round(predicted_mb, 2)) # Ensures AWS Lambda minimum of 128MB
    
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
        
        # THE CONVERSION FACTOR (TRANSLATION LAYER) 
        # Google Borg uses "CPU Cores". AWS uses "Invocations".
        # We assume 200 AWS Invocations equal roughly 1 Google CPU Core of load.
        INVOCATION_TO_CPU_RATIO = 200.0
        
        for i, raw_invocations in enumerate(resampled_history):
            step_time = minute_index - ((11-i) * 5)
            hour = (step_time // 60) % 24
            min_of_hour = step_time % 60
            
            # Map huge AWS invocations down to small CPU Units for the LSTM
            mapped_cpu = raw_invocations / INVOCATION_TO_CPU_RATIO
            
            cpu_avg = mapped_cpu
            cpu_max = mapped_cpu * 1.5      
            mem_avg = mapped_cpu * 0.8      
            assigned_mem = 0.5           
            
            traffic_features.append([cpu_avg, cpu_max, mem_avg, assigned_mem])
            time_features.append([hour, min_of_hour])

        traffic_scaled = self.traffic_scaler.transform(np.array(traffic_features))
        time_scaled = self.time_scaler.transform(np.array(time_features))
        combined_data = np.hstack([traffic_scaled, time_scaled])
        
        input_tensor = torch.tensor(combined_data, dtype=torch.float32).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            pred_scaled = self.optimizer_model(input_tensor).cpu().numpy()
            
        dummy_pred = np.zeros((1, 4))
        dummy_pred[0, 0] = pred_scaled[0, 0]
        pred_cpu_units = self.traffic_scaler.inverse_transform(dummy_pred)[0, 0]
        
        #  CONVERT BACK TO INVOCATIONS 
        # Multiply back so the Streamlit graph shows 1000+ instead of 5
        predicted_invocations = pred_cpu_units * INVOCATION_TO_CPU_RATIO
        
        return max(0.0, float(predicted_invocations))