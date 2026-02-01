# import time
# import pandas as pd
# import numpy as np
# from smartscale_core import SmartScaleSystem 
# import os

# # --- CONFIGURATION ---
# DATA_FILE = "../data/google_cluster_traffic.csv"
# SIMULATION_SPEED = 0.05  # Delay in seconds (Lower = Faster Simulation)
# HISTORY_WINDOW = 120     # How far back the model looks

# class SmartScaleSimulator:
#     def __init__(self):
#         print("🚀 Starting SmartScale Simulation Server...")
        
#         # 1. Initialize the AI System
#         self.brain = SmartScaleSystem()
        
#         # 2. Load Traffic Data (The "Virtual World")
#         if os.path.exists(DATA_FILE):
#             self.df = pd.read_csv(DATA_FILE)
#             print(f"   📂 Loaded Traffic Data: {len(self.df)} minutes")
#         else:
#             print("   ❌ Error: Traffic file not found!")
#             exit()
            
#         # 3. Create Log File (To store results for the Dashboard)
#         self.log_file = "simulation_logs.csv"
#         with open(self.log_file, "w") as f:
#             f.write("time,actual_load,predicted_load,replicas,decision\n")

#     def run(self):
#         print("\n🔴 SIMULATION LIVE: Streaming Google Cluster Data...")
#         print(f"{'TIME':<10} | {'ACTUAL':<10} | {'PREDICTED':<10} | {'REPLICAS':<10} | {'DECISION'}")
#         print("-" * 65)

#         history_buffer = []

#         # Loop through the CSV file
#         for index, row in self.df.iterrows():
#             minute = int(row['minute'])
#             actual_load = float(row['cpu_load'])
            
#             # 1. Update History Buffer
#             history_buffer.append(actual_load)
#             if len(history_buffer) > HISTORY_WINDOW:
#                 history_buffer.pop(0) # Keep only last 120 mins
            
#             # 2. Get Prediction from AI (Only if we have enough history)
#             predicted_load = 0.0
#             if len(history_buffer) == HISTORY_WINDOW:
#                 predicted_load = self.brain.predict_next_load(history_buffer)

#             # 3. SCALING LOGIC (The "Auto-Scaler")
#             # Logic: 1 Replica handles 5 CPU units (Arbitrary rule for demo)
#             needed_replicas = max(1, int(np.ceil(predicted_load / 5.0)))
            
#             # Decision String
#             decision = "MAINTAIN"
#             if predicted_load > actual_load * 1.2: decision = "SCALE UP 🔼"
#             elif predicted_load < actual_load * 0.8: decision = "SCALE DOWN 🔽"

#             # 4. Log to Terminal
#             # We skip printing every single line to keep terminal clean (print every 10th)
#             if index % 10 == 0:
#                 print(f"{minute:<10} | {actual_load:<10.4f} | {predicted_load:<10.4f} | {needed_replicas:<10} | {decision}")

#             # 5. Save to Log File (For the Dashboard)
#             with open(self.log_file, "a") as f:
#                 f.write(f"{minute},{actual_load},{predicted_load},{needed_replicas},{decision}\n")

#             # 6. Wait (Simulate time passing)
#             time.sleep(SIMULATION_SPEED)

# if __name__ == "__main__":
#     sim = SmartScaleSimulator()
#     sim.run()



import time
import pandas as pd
import numpy as np
from smartscale_core import SmartScaleSystem 
import os

# --- PATH CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # .../core_system
# Locate Data in ../data/
DATA_FILE = os.path.join(os.path.dirname(BASE_DIR), "data", "google_cluster_traffic.csv")
# Save Logs to ../frontend/simulation_logs.csv (So Dashboard can see it!)
LOG_FILE = os.path.join(os.path.dirname(BASE_DIR), "frontend", "simulation_logs.csv")

SIMULATION_SPEED = 0.05
HISTORY_WINDOW = 120

class SmartScaleSimulator:
    def __init__(self):
        print("🚀 Starting SmartScale Simulation Server...")
        self.brain = SmartScaleSystem()
        
        if os.path.exists(DATA_FILE):
            self.df = pd.read_csv(DATA_FILE)
            print(f"   📂 Loaded Traffic Data: {len(self.df)} minutes")
        else:
            print(f"   ❌ Error: Traffic file not found at {DATA_FILE}")
            exit()
            
        # Create Log File
        self.log_file = LOG_FILE
        with open(self.log_file, "w") as f:
            f.write("time,actual_load,predicted_load,replicas,decision\n")
        print(f"   📝 Logging to: {self.log_file}")

    def run(self):
        print("\n🔴 SIMULATION LIVE: Streaming Google Cluster Data...")
        print(f"{'TIME':<10} | {'ACTUAL':<10} | {'PREDICTED':<10} | {'REPLICAS':<10} | {'DECISION'}")
        print("-" * 65)
        history_buffer = []

        for index, row in self.df.iterrows():
            minute = int(row['minute'])
            actual_load = float(row['cpu_load'])
            history_buffer.append(actual_load)
            if len(history_buffer) > HISTORY_WINDOW: history_buffer.pop(0)
            
            predicted_load = 0.0
            if len(history_buffer) == HISTORY_WINDOW:
                predicted_load = self.brain.predict_next_load(history_buffer)

            needed_replicas = max(1, int(np.ceil(predicted_load / 5.0)))
            decision = "MAINTAIN"
            if predicted_load > actual_load * 1.2: decision = "SCALE UP 🔼"
            elif predicted_load < actual_load * 0.8: decision = "SCALE DOWN 🔽"

            if index % 10 == 0:
                print(f"{minute:<10} | {actual_load:<10.4f} | {predicted_load:<10.4f} | {needed_replicas:<10} | {decision}")

            with open(self.log_file, "a") as f:
                f.write(f"{minute},{actual_load},{predicted_load},{needed_replicas},{decision}\n")

            time.sleep(SIMULATION_SPEED)

if __name__ == "__main__":
    sim = SmartScaleSimulator()
    sim.run()