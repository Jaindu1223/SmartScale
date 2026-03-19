import pandas as pd
import ast
import numpy as np

# Load your RAW google trace data
RAW_DATA_FILE = "/Users/jaindugajanayake/Desktop/4th Yr Docs/FYP/SmartScale/data/originalDataSet/borg_traces_data.csv" # Update with your actual raw file name
print(f"🔍 Loading Raw Google Trace Log: {RAW_DATA_FILE}")
df = pd.read_csv(RAW_DATA_FILE)

# Safely parse the stringified dictionaries for CPU and Memory
def parse_dict_string(dict_str):
    if pd.isna(dict_str) or dict_str == "[]":
        return {'cpus': 0.0, 'memory': 0.0}
    try:
        return ast.literal_eval(dict_str)
    except:
        return {'cpus': 0.0, 'memory': 0.0}

print("⚙️ Extracting Multi-Variate Hardware Features...")

# 1. Extract CPU and Memory from dictionaries
df['avg_usage_dict'] = df['average_usage'].apply(parse_dict_string)
df['cpu_avg'] = df['avg_usage_dict'].apply(lambda x: x.get('cpus', 0.0))
df['mem_avg'] = df['avg_usage_dict'].apply(lambda x: x.get('memory', 0.0))

df['max_usage_dict'] = df['maximum_usage'].apply(parse_dict_string)
df['cpu_max'] = df['max_usage_dict'].apply(lambda x: x.get('cpus', 0.0))

# 2. Clean assigned_memory (fill blanks with 0)
df['assigned_mem'] = df['assigned_memory'].fillna(0.0)

# 3. Create a Time Index (convert microseconds to minutes)
df['minute'] = (df['start_time'] / 1e6 / 60).astype(int)

# 4. Group by minute to get the total load across the cluster
print("📊 Aggregating cluster traffic by minute...")
cluster_traffic = df.groupby('minute').agg({
    'cpu_avg': 'sum',
    'cpu_max': 'max',  # Get the highest spike in that minute
    'mem_avg': 'sum',
    'assigned_mem': 'sum'
}).reset_index()

# 5. Apply the "Smoothing" fix we discussed earlier (Rolling Average)
print("🌊 Smoothing data to remove chaotic micro-noise...")
# We smooth the average metrics, but leave the max spike alone so the AI learns to catch it!
cluster_traffic['cpu_avg'] = cluster_traffic['cpu_avg'].rolling(window=3, min_periods=1).mean()
cluster_traffic['mem_avg'] = cluster_traffic['mem_avg'].rolling(window=3, min_periods=1).mean()

# Save the rich dataset
output_file = "/Users/jaindugajanayake/Desktop/4th Yr Docs/FYP/SmartScale/data/google_trace_log_2019.csv"
cluster_traffic.to_csv(output_file, index=False)
print(f"✅ Saved highly optimized dataset as: {output_file}")