import pandas as pd
import numpy as np
import tensorflow as tf

run_df = pd.read_csv('/ml-model/running_time_series.csv').dropna(subset=['heartrate', 'watts'])
bike_df = pd.read_csv('/ml-model/biking_time_series.csv')

min_hr = min(run_df['heartrate'].min(), bike_df['heartrate'].min())
max_hr = max(run_df['heartrate'].max(), bike_df['heartrate'].max())
max_time = max(run_df['time_offset'].max(), bike_df['time_offset'].max())

# Every HR above rest == X Watts produced
rest_hr = 60.0
avg_run_hr = run_df['heartrate'].mean()
avg_run_watts = run_df['watts'].mean()
fitness_slope = avg_run_watts / (avg_run_hr - rest_hr)

n = 20000
synthetic_hr = np.random.uniform(min_hr, max_hr, n)
synthetic_time = np.random.uniform(0, max_time, n)
synthetic_speed = np.random.uniform(2, 12, n) # meters / sec
synthetic_mode = np.random.randint(0, 2, n)   # 0: long distance, 1: HIIT

# Watts / speed = required resistance
predicted_watts = (synthetic_hr - rest_hr) * fitness_slope
# Increase intensity for HIIT Mode
predicted_watts = np.where(synthetic_mode == 1, predicted_watts * 1.3, predicted_watts)

# Convert to servo angle (0-180). 2.2 calibrates the resistance calculation (will be adjusted later!)
target_angle = np.clip((predicted_watts / synthetic_speed) * 2.2, 0, 180)

X = np.column_stack([synthetic_hr, synthetic_speed, synthetic_time, synthetic_mode]).astype(np.float32)
y = target_angle.astype(np.float32)

model = tf.keras.Sequential([
    tf.keras.layers.Dense(32, activation='relu', input_shape=(4,)),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(1, activation='linear')
])
model.compile(optimizer='adam', loss='mse')
model.fit(X, y, epochs=15, batch_size=32, verbose=0)

converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()
with open("bike_prediction_model.tflite", "wb") as f:
    f.write(tflite_model)

print("SUCCESS: 'bike_prediction_model.tflite' generated.")

