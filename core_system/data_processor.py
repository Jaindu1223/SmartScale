import numpy as np
from sklearn.preprocessing import MinMaxScaler

def prepare_lstm_input(cloudwatch_values, sequence_length=15):
    """
    Converts raw CloudWatch metrics into the 3D tensor shape required by Keras LSTMs.
    """
    if len(cloudwatch_values) < sequence_length:
        return None, None
        
    # Reshape into a 2D array for the Scaler
    data_array = np.array(cloudwatch_values).reshape(-1, 1)
    
    # Normalize the data between 0 and 1
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data_array)
    
    # Extract only the most recent sequence for a live prediction
    recent_sequence = scaled_data[-sequence_length:]
    
    # Reshape into 3D for Keras: (batch_size, time_steps, features)
    lstm_input = recent_sequence.reshape(1, sequence_length, 1)
    
    return lstm_input, scaler