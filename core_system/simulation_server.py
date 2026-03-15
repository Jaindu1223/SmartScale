import time
import pandas as pd
import numpy as np
from smartscale_core import SmartScaleSystem 
import os

# --- PATH CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(os.path.dirname(BASE_DIR), "data", "google_cluster_traffic.csv")
LOG_FILE = os.path.join(os.path.dirname(BASE_DIR), "frontend", "simulation_logs.csv")

# --- SETTINGS ---
SIMULATION_SPEED = 0.05  
HISTORY_WINDOW = 120     

class SmartScaleSimulator:
    def __init__(self):
        print("Starting SmartScale Simulation Server...")
        self.brain = SmartScaleSystem()
        
        # Load the Data
        if os.path.exists(DATA_FILE):
            raw_df = pd.read_csv(DATA_FILE)
            
            # --- RESAMPLE TO CONTINUOUS 1-MINUTE INTERVALS ---
            print(f"    Processing Data: Filling time gaps in Google Trace...")
            
            # 1. Set 'minute' as the index
            raw_df = raw_df.sort_values('minute').set_index('minute')
            
            # 2. Create a full index from Min to Max (0, 1, 2, 3... end)
            full_idx = np.arange(raw_df.index.min(), raw_df.index.max() + 1)
            
            # 3. Reindex and Interpolate (Fill blanks linearly)
            self.df = raw_df.reindex(full_idx)
            self.df['cpu_load'] = self.df['cpu_load'].interpolate(method='linear')
            
            # 4. Reset index so 'minute' is a column again
            self.df = self.df.reset_index().rename(columns={'index': 'minute'})
            
            # 5. LIMIT TO 2000 MINUTES (Now these are 2000 *continuous* minutes)
            self.df = self.df.head(2000)
            
            print(f"    Ready: {len(self.df)} continuous minutes loaded for simulation.")
        else:
            print(f"    Error: Traffic file not found at {DATA_FILE}")
            exit()
            
        # Initialize Log File
        self.log_file = LOG_FILE
        with open(self.log_file, "w") as f:
            f.write("time,actual_load,predicted_load,replicas,decision\n")
        print(f"    Logging to: {self.log_file}")


    #iterate through each minute in the data and simulate the scaling decisions in simulation_server.py file
    def run(self):
        print("\n SIMULATION LIVE: Streaming Continuous Data...")
        print(f"{'TIME':<10} | {'ACTUAL':<10} | {'PREDICTED':<10} | {'REPLICAS':<10} | {'DECISION'}")
        print("-" * 65)
        
        history_buffer = []

        for index, row in self.df.iterrows():
            minute = int(row['minute'])
            # Fill NaN with 0 just in case interpolation missed start/end
            actual_load = float(row['cpu_load']) if not pd.isna(row['cpu_load']) else 0.0
            
            # 1. Update History Buffer
            history_buffer.append(actual_load)
            if len(history_buffer) > HISTORY_WINDOW: 
                history_buffer.pop(0) 
            
            # 2. Get Prediction from AI
            predicted_load = 0.0
            
            if len(history_buffer) >= 60:
                predicted_load = self.brain.predict_next_load(history_buffer, minute)

            # 3. HYBRID SCALING LOGIC
            effective_load = max(actual_load, predicted_load)
            needed_replicas = max(1, int(np.ceil(effective_load / 5.0)))
            
            decision = "MAINTAIN"
            if predicted_load > actual_load * 1.2: 
                decision = "SCALE UP"
            elif actual_load > predicted_load * 2.0:
                decision = "REACTIVE UP"
            elif effective_load < actual_load * 0.8: 
                decision = "SCALE DOWN"

            # 4. Log to Terminal
            if index % 10 == 0:
                print(f"{minute:<10} | {actual_load:<10.4f} | {predicted_load:<10.4f} | {needed_replicas:<10} | {decision}")

            # 5. Write to CSV
            with open(self.log_file, "a") as f:
                f.write(f"{minute},{actual_load},{predicted_load},{needed_replicas},{decision}\n")

            time.sleep(SIMULATION_SPEED)
            
        print("\n Simulation Completed (2000 Minutes Reached).")

if __name__ == "__main__":
    sim = SmartScaleSimulator()
    sim.run()