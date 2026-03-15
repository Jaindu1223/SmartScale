import time
import numpy as np
from datetime import datetime, timezone
import os
import sys

# --- PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path: sys.path.insert(0, project_root)

from core_system.smartscale_core import SmartScaleSystem
from core_system.metrics_collector import get_lambda_metrics
from aws_utils import scale_aws_resource, AWS_FUNC, AWS_ACCESS, AWS_SECRET, AWS_REGION

def execute_monitor():
    print("\n Starting SmartScale Autonomic Manager (CLI Mode)")
    print("Press Ctrl+C to stop monitoring.\n")
    
    try:
        brain = SmartScaleSystem()
    except Exception as e:
        print(f" Failed to load AI Brain: {e}")
        return

    last_processed_time = None
    last_scaled_replica = 1

    print(f"| {'Time':<10} | {'Actual Load':<12} | {'Predicted Load':<15} | {'Replicas':<8} | {'Decision':<12} |")
    print("-" * 73)

    try:
        while True:
            ts, counts = get_lambda_metrics(AWS_FUNC, AWS_ACCESS, AWS_SECRET, AWS_REGION)
            
            if len(ts) > 0:
                latest_time_str = ts[-1].strftime("%H:%M:%S")
                latest_actual = counts[-1]
                
                if last_processed_time != latest_time_str:
                    live_pred = brain.predict_live_load(list(counts), datetime.now(timezone.utc))
                    replicas = max(1, int(np.ceil(live_pred / 50.0)))
                    
                    if replicas > last_scaled_replica: decision = "SCALE UP "
                    elif replicas < last_scaled_replica: decision = "SCALE DOWN "
                    else: decision = "MAINTAIN "
                    
                    if replicas != last_scaled_replica:
                        success = scale_aws_resource(replicas)
                        if success: last_scaled_replica = replicas
                    
                    print(f"| {latest_time_str:<10} | {latest_actual:<12.0f} | {live_pred:<15.0f} | {replicas:<8} | {decision:<12} |")
                    last_processed_time = latest_time_str
            
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n\n SmartScale CLI Monitor Stopped Safely.\n")