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



# import time
# import pandas as pd
# import numpy as np
# from smartscale_core import SmartScaleSystem 
# import os

# # --- PATH CONFIGURATION ---
# BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # .../core_system
# # Locate Data in ../data/
# DATA_FILE = os.path.join(os.path.dirname(BASE_DIR), "data", "google_cluster_traffic.csv")
# # Save Logs to ../frontend/simulation_logs.csv (So Dashboard can see it!)
# LOG_FILE = os.path.join(os.path.dirname(BASE_DIR), "frontend", "simulation_logs.csv")

# SIMULATION_SPEED = 0.05
# HISTORY_WINDOW = 120

# class SmartScaleSimulator:
#     def __init__(self):
#         print("🚀 Starting SmartScale Simulation Server...")
#         self.brain = SmartScaleSystem()
        
#         if os.path.exists(DATA_FILE):
#             self.df = pd.read_csv(DATA_FILE)
#             print(f"   📂 Loaded Traffic Data: {len(self.df)} minutes")
#         else:
#             print(f"   ❌ Error: Traffic file not found at {DATA_FILE}")
#             exit()
            
#         # Create Log File
#         self.log_file = LOG_FILE
#         with open(self.log_file, "w") as f:
#             f.write("time,actual_load,predicted_load,replicas,decision\n")
#         print(f"   📝 Logging to: {self.log_file}")

#     def run(self):
#         print("\n🔴 SIMULATION LIVE: Streaming Google Cluster Data...")
#         print(f"{'TIME':<10} | {'ACTUAL':<10} | {'PREDICTED':<10} | {'REPLICAS':<10} | {'DECISION'}")
#         print("-" * 65)
#         history_buffer = []

#         for index, row in self.df.iterrows():
#             minute = int(row['minute'])
#             actual_load = float(row['cpu_load'])
#             history_buffer.append(actual_load)
#             if len(history_buffer) > HISTORY_WINDOW: history_buffer.pop(0)
            
#             predicted_load = 0.0
#             if len(history_buffer) == HISTORY_WINDOW:
#                 predicted_load = self.brain.predict_next_load(history_buffer)

#             needed_replicas = max(1, int(np.ceil(predicted_load / 5.0)))
#             decision = "MAINTAIN"
#             if predicted_load > actual_load * 1.2: decision = "SCALE UP 🔼"
#             elif predicted_load < actual_load * 0.8: decision = "SCALE DOWN 🔽"

#             if index % 10 == 0:
#                 print(f"{minute:<10} | {actual_load:<10.4f} | {predicted_load:<10.4f} | {needed_replicas:<10} | {decision}")

#             with open(self.log_file, "a") as f:
#                 f.write(f"{minute},{actual_load},{predicted_load},{needed_replicas},{decision}\n")

#             time.sleep(SIMULATION_SPEED)

# if __name__ == "__main__":
#     sim = SmartScaleSimulator()
#     sim.run()





# import time
# import pandas as pd
# import numpy as np
# from smartscale_core import SmartScaleSystem 
# import os

# # --- PATH CONFIGURATION ---
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DATA_FILE = os.path.join(os.path.dirname(BASE_DIR), "data", "google_cluster_traffic.csv")
# LOG_FILE = os.path.join(os.path.dirname(BASE_DIR), "frontend", "simulation_logs.csv")

# SIMULATION_SPEED = 0.05
# HISTORY_WINDOW = 120 # Still keep a buffer, Core handles the resampling

# class SmartScaleSimulator:
#     def __init__(self):
#         print("🚀 Starting SmartScale Simulation Server...")
#         self.brain = SmartScaleSystem()
        
#         if os.path.exists(DATA_FILE):
#             self.df = pd.read_csv(DATA_FILE)
#             print(f"   📂 Loaded Traffic Data: {len(self.df)} minutes")
#         else:
#             print(f"   ❌ Error: Traffic file not found at {DATA_FILE}")
#             exit()
            
#         self.log_file = LOG_FILE
#         with open(self.log_file, "w") as f:
#             f.write("time,actual_load,predicted_load,replicas,decision\n")
#         print(f"   📝 Logging to: {self.log_file}")

#     def run(self):
#         print("\n🔴 SIMULATION LIVE: Streaming Google Cluster Data...")
#         print(f"{'TIME':<10} | {'ACTUAL':<10} | {'PREDICTED':<10} | {'REPLICAS':<10} | {'DECISION'}")
#         print("-" * 65)
#         history_buffer = []

#         for index, row in self.df.iterrows():
#             minute = int(row['minute'])
#             actual_load = float(row['cpu_load'])
            
#             history_buffer.append(actual_load)
#             if len(history_buffer) > HISTORY_WINDOW: history_buffer.pop(0)
            
#             predicted_load = 0.0
            
#             # We need at least 60 minutes of data for the new model
#             if len(history_buffer) >= 60:
#                 # UPDATED: Pass 'minute' so Core knows the time
#                 predicted_load = self.brain.predict_next_load(history_buffer, minute)

#             needed_replicas = max(1, int(np.ceil(predicted_load / 5.0)))
#             decision = "MAINTAIN"
#             if predicted_load > actual_load * 1.2: decision = "SCALE UP 🔼"
#             elif predicted_load < actual_load * 0.8: decision = "SCALE DOWN 🔽"

#             if index % 10 == 0:
#                 print(f"{minute:<10} | {actual_load:<10.4f} | {predicted_load:<10.4f} | {needed_replicas:<10} | {decision}")

#             with open(self.log_file, "a") as f:
#                 f.write(f"{minute},{actual_load},{predicted_load},{needed_replicas},{decision}\n")

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
# This ensures the script works no matter where you run it from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(os.path.dirname(BASE_DIR), "data", "google_cluster_traffic.csv")
# Save Logs to ../frontend/simulation_logs.csv (So Dashboard can see it!)
LOG_FILE = os.path.join(os.path.dirname(BASE_DIR), "frontend", "simulation_logs.csv")

# --- SETTINGS ---
SIMULATION_SPEED = 0.05  # Speed of the simulation (0.05s per minute)
HISTORY_WINDOW = 120     # Keep enough history for the brain

class SmartScaleSimulator:
    def __init__(self):
        print("🚀 Starting SmartScale Simulation Server...")
        self.brain = SmartScaleSystem()
        
        # Load the Data
        if os.path.exists(DATA_FILE):
            self.df = pd.read_csv(DATA_FILE)
            print(f"   📂 Loaded Traffic Data: {len(self.df)} minutes")
        else:
            print(f"   ❌ Error: Traffic file not found at {DATA_FILE}")
            exit()
            
        # Initialize Log File
        self.log_file = LOG_FILE
        with open(self.log_file, "w") as f:
            f.write("time,actual_load,predicted_load,replicas,decision\n")
        print(f"   📝 Logging to: {self.log_file}")

    def run(self):
        print("\n🔴 SIMULATION LIVE: Streaming Google Cluster Data...")
        print(f"{'TIME':<10} | {'ACTUAL':<10} | {'PREDICTED':<10} | {'REPLICAS':<10} | {'DECISION'}")
        print("-" * 65)
        
        history_buffer = []

        # Iterate through the CSV rows simulating time passing
        for index, row in self.df.iterrows():
            minute = int(row['minute'])
            actual_load = float(row['cpu_load'])
            
            # 1. Update History Buffer
            history_buffer.append(actual_load)
            if len(history_buffer) > HISTORY_WINDOW: 
                history_buffer.pop(0) 
            
            # 2. Get Prediction from AI
            predicted_load = 0.0
            
            # We need at least 60 minutes of data for the new LSTM model
            if len(history_buffer) >= 60:
                # Pass 'minute' so the Core can calculate time features (Hour/Min)
                predicted_load = self.brain.predict_next_load(history_buffer, minute)

            # 3. HYBRID SCALING LOGIC (The Safety Net)
            # ---------------------------------------------------------
            # Rule: Use the HIGHER of (Actual, Predicted).
            # If AI predicts a spike, we scale up early (Proactive).
            # If AI misses a spike, we scale based on Actual (Reactive Safety).
            effective_load = max(actual_load, predicted_load)
            
            # Calculate needed replicas (Assuming 1 Replica handles 5.0 CPU Load)
            needed_replicas = max(1, int(np.ceil(effective_load / 5.0)))
            
            # Decision Logic for Display
            decision = "MAINTAIN"
            
            # If we are scaling based on a prediction that is much higher than now -> Proactive
            if predicted_load > actual_load * 1.2: 
                decision = "SCALE UP 🔼"
            # If AI missed it, but Actual is high -> Reactive Safety
            elif actual_load > predicted_load * 2.0:
                decision = "REACTIVE UP ⚠️"
            # If scaling down
            elif effective_load < actual_load * 0.8: 
                decision = "SCALE DOWN 🔽"

            # 4. Log to Terminal (Every 10th step to keep it readable)
            if index % 10 == 0:
                print(f"{minute:<10} | {actual_load:<10.4f} | {predicted_load:<10.4f} | {needed_replicas:<10} | {decision}")

            # 5. Write to CSV for Dashboard
            with open(self.log_file, "a") as f:
                f.write(f"{minute},{actual_load},{predicted_load},{needed_replicas},{decision}\n")

            # 6. Simulate Delay
            time.sleep(SIMULATION_SPEED)

if __name__ == "__main__":
    sim = SmartScaleSimulator()
    sim.run()