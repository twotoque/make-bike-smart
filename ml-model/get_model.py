import pandas as pd
import numpy as np
import tensorflow as tf
from datetime import datetime
import os

FEEDBACK_WEIGHT = 3  # each feedback sample counts as 3 synthetic samples
HIIT_ADJUSTMENT_FACTOR = 1.2  # HIIT mode increases predicted watts by 20%
REST_HR = 60.0

# load strava data 
run_df = pd.read_csv('/Users/dereksong/Documents/make-bike-smart/ml-model/running_time_series.csv').dropna(subset=['heartrate', 'watts'])
bike_df = pd.read_csv('/Users/dereksong/Documents/make-bike-smart/ml-model/biking_time_series.csv')

min_hr = min(run_df['heartrate'].min(), bike_df['heartrate'].min())
max_hr = max(run_df['heartrate'].max(), bike_df['heartrate'].max())
max_time = max(run_df['time_offset'].max(), bike_df['time_offset'].max())


avg_run_hr = run_df['heartrate'].mean()
avg_run_watts = run_df['watts'].mean()
fitness_slope = avg_run_watts / (avg_run_hr - REST_HR)

# generate synthetic training data
n = 20000
synthetic_hr = np.random.uniform(min_hr, max_hr, n)
synthetic_time = np.random.uniform(0, max_time, n)
synthetic_speed = np.random.uniform(2, 12, n)
synthetic_mode = np.random.randint(0, 2, n)

predicted_watts = (synthetic_hr - REST_HR) * fitness_slope
predicted_watts = np.where(synthetic_mode == 1, predicted_watts * HIIT_ADJUSTMENT_FACTOR, predicted_watts)
target_angle = np.clip((predicted_watts / synthetic_speed) * 2.2, 0, 180)

X_initial = np.column_stack([synthetic_hr, synthetic_speed, synthetic_time, synthetic_mode]).astype(np.float32)
y_initial = target_angle.astype(np.float32)

# load feedback data if exists 
feedback_file = '/Users/dereksong/Documents/make-bike-smart/ml-model/user_feedback.csv'

if os.path.exists(feedback_file):
    print("Loading existing feedback data...")
    feedback_df = pd.read_csv(feedback_file)
    
    X_feedback = feedback_df[['heartrate', 'speed', 'time_offset', 'mode']].values.astype(np.float32)
    y_feedback = feedback_df['adjusted_angle'].values.astype(np.float32)
    
    X_feedback_weighted = np.repeat(X_feedback, FEEDBACK_WEIGHT, axis=0)
    y_feedback_weighted = np.repeat(y_feedback, FEEDBACK_WEIGHT)
    
    X_combined = np.vstack([X_initial, X_feedback_weighted])
    y_combined = np.concatenate([y_initial, y_feedback_weighted])
    
    print(f"Training with {len(X_initial)} synthetic + {len(X_feedback)} feedback samples (weighted {FEEDBACK_WEIGHT}x)")
else:
    print("No feedback data found. Using synthetic data only.")
    X_combined = X_initial
    y_combined = y_initial

# train model with combined 
model = tf.keras.Sequential([
    tf.keras.layers.Dense(32, activation='relu', input_shape=(4,)),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(1, activation='linear')
])
model.compile(optimizer='adam', loss='mse')
model.fit(X_combined, y_combined, epochs=15, batch_size=32, verbose=0)

# export
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()
with open("bike_prediction_model.tflite", "wb") as f:
    f.write(tflite_model)

print("bike_prediction_model.tflite generated with feedback integration.")

def save_feedback(heartrate, speed, time_offset, mode, current_angle, feedback_type):
    """
    Call this function from your Swift app when user provides feedback.
    
    Args:
        heartrate: Current heart rate (BPM)
        speed: Current speed (m/s)
        time_offset: Time into workout (seconds)
        mode: 0 for Long Distance, 1 for HIIT
        current_angle: The angle the model predicted
        feedback_type: "good", "too_easy", or "too_hard"
    """
    # adjust angle based on feedback
    if feedback_type == "too_easy":
        adjusted_angle = min(current_angle + 15, 180)  
    elif feedback_type == "too_hard":
        adjusted_angle = max(current_angle - 15, 0)    
    else: 
        adjusted_angle = current_angle
    
    # feedback record payload 
    feedback_record = {
        'timestamp': datetime.now().isoformat(),
        'heartrate': heartrate,
        'speed': speed,
        'time_offset': time_offset,
        'mode': mode,
        'predicted_angle': current_angle,
        'feedback': feedback_type,
        'adjusted_angle': adjusted_angle
    }
    
    # Append to CSV
    df = pd.DataFrame([feedback_record])
    
    if os.path.exists(feedback_file):
        df.to_csv(feedback_file, mode='a', header=False, index=False)
    else:
        df.to_csv(feedback_file, mode='w', header=True, index=False)
    
    print(f"Feedback saved: {feedback_type} (angle: {current_angle} -> {adjusted_angle})")
    return 