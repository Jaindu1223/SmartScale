import sys
import os
import time
from datetime import datetime
import random

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

from core_system.smartscale_core import SmartScaleSystem

print("Loading SmartScale Core and initializing test environment...")

# Initialize the brain ( loads the .pth files into memory)
system = SmartScaleSystem()

# Generate 60 minutes of dummy traffic history (e.g., between 100 and 1000 invocations)
dummy_history = [random.randint(100, 1000) for _ in range(60)]
current_time = datetime.now()

print("\nStarting backend performance profiling (100 iterations)...")
execution_times = []

#  EXECUTION PHASE (Strictly Timed)
for i in range(100):
    start_time = time.time()
    
    #  Execute the forward pass through the Proactive LSTM
    predicted_invocations = system.predict_live_load(dummy_history, current_time)
    
    # Formulate the Boto3 scaling decision
    # (Calculating how many replicas are needed based on the AI prediction)
    replicas_needed = max(1, int(predicted_invocations / 100)) 
    
    # stopping the timer here! 
    # This proves the system calculates the decision in under 100ms.
    # We do not time the actual AWS HTTP network transmission over the ocean.
    
    end_time = time.time()
    execution_times.append((end_time - start_time) * 1000) # Convert to milliseconds

# print metrics
avg_time = sum(execution_times) / len(execution_times)
max_time = max(execution_times)
min_time = min(execution_times)

print("-" * 55)
print("SmartScale Autonomic Controller - Decision Latency Profile")
print("-" * 55)
print(f"Iterations:             100 runs")
print(f"Minimum Latency:        {min_time:.2f} ms")
print(f"Maximum Latency:        {max_time:.2f} ms")
print(f"Average Decision Time:  {avg_time:.2f} ms")
print("-" * 55)

if avg_time < 100:
    print("Status: PASS (Sub-100ms NFR02 requirement met)")
else:
    print("Status: FAIL (Latency exceeded 100ms)")