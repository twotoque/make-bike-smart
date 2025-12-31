import pandas as pd
import numpy as np
import tensorflow as tf
from datetime import datetime
import os
import json

FEEDBACK_FILE = '/Users/dereksong/Documents/make-bike-smart/ml-model/user_feedback.csv'
ANGLE_DIFF_FILE = '/Users/dereksong/Documents/make-bike-smart/ml-model/angle_differences.json'
FEEDBACK_WEIGHT = 5
HIIT_ADJUSTMENT_FACTOR = 1.3
REST_HR = 60.0

angle_differences = []

run_df = pd.read_csv('/Users/dereksong/Documents/make-bike-smart/ml-model/running_time_series.csv').dropna(subset=['heartrate', 'watts'])
bike_df = pd.read_csv('/Users/dereksong/Documents/make-bike-smart/ml-model/biking_time_series.csv')

def load_angle_differences():
    """Load previous angle differences from file"""
    global angle_differences
    if os.path.exists(ANGLE_DIFF_FILE):
        with open(ANGLE_DIFF_FILE, 'r') as f:
            angle_differences = json.load(f)
        print(f"Loaded {len(angle_differences)} previous angle difference records\n")

def save_angle_difference(scenario_desc, hr, speed, time, mode, before_angle, after_angle):
    """Save angle difference to global array and file"""
    global angle_differences

    diff_record = {
        'timestamp': datetime.now().isoformat(),
        'scenario': scenario_desc,
        'hr': int(hr),
        'speed': float(speed),
        'time': int(time),
        'mode': 'HIIT' if mode == 1 else 'Long',
        'angle_before': round(float(before_angle), 2),
        'angle_after': round(float(after_angle), 2),
        'difference': round(float(after_angle - before_angle), 2)
    }

    angle_differences.append(diff_record)
    
    # Save to file
    with open(ANGLE_DIFF_FILE, 'w') as f:
        json.dump(angle_differences, f, indent=2)
    
    print(f"\nAngle Change Recorded:")
    print(f"   Before: {before_angle:.2f}° → After: {after_angle:.2f}° | Δ = {diff_record['difference']:.2f}°")

def save_feedback(heartrate, speed, time_offset, mode, current_angle, feedback_type):
    """
    save user feedback to CSV
    """
    if feedback_type == "too_easy":
        adjusted_angle = min(current_angle + 15, 180)  
    elif feedback_type == "too_hard":
        adjusted_angle = max(current_angle - 15, 0)    
    else: 
        adjusted_angle = current_angle
    
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
    
    df = pd.DataFrame([feedback_record])
    
    if os.path.exists(FEEDBACK_FILE):
        df.to_csv(FEEDBACK_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(FEEDBACK_FILE, mode='w', header=True, index=False)
    
    print(f"Feedback saved: {feedback_type} (angle: {current_angle:.1f}° → {adjusted_angle:.1f}°)")

def retrain_model():
    """
    Retrain the model with current feedback data
    """
    print("\nRetraining model...")
    
    # load historical data

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
    if os.path.exists(FEEDBACK_FILE):
        feedback_df = pd.read_csv(FEEDBACK_FILE)
        
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

    # train with combine data
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(32, activation='relu', input_shape=(4,)),
        tf.keras.layers.Dense(16, activation='relu'),
        tf.keras.layers.Dense(1, activation='linear')
    ])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X_combined, y_combined, epochs=15, batch_size=32, verbose=0)

    # save updated model in tflite 
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    with open("bike_prediction_model.tflite", "wb") as f:
        f.write(tflite_model)

    print("Model retrained and saved to bike_prediction_model.tflite\n")

def run_interactive_test():
    # load previous angle differences
    load_angle_differences()
    
    interpreter = tf.lite.Interpreter(model_path="bike_prediction_model.tflite")
    interpreter.allocate_tensors()
    in_idx = interpreter.get_input_details()[0]['index']
    out_idx = interpreter.get_output_details()[0]['index']
    
    scenarios = [
        {"desc": "Warmup (Steady)", "hr": 105, "speed": 4.0, "time": 120, "mode": 0},
        {"desc": "HIIT Sprint Start", "hr": 140, "speed": 9.0, "time": 600, "mode": 1},
        {"desc": "Deep in Sprint", "hr": 175, "speed": 10.5, "time": 630, "mode": 1},
        {"desc": "Long Distance Cruise", "hr": 135, "speed": 6.0, "time": 1800, "mode": 0}
    ]
    
    current_scenario = 0
    angle_before_retrain = None
    
    print("\n" + "="*70)
    print("INTERACTIVE BIKE MODEL TESTER")
    print("="*70)
    print("\nControls:")
    print("  [N] Next scenario")
    print("  [F] Add feedback (good/easy/hard)")
    print("  [G] Retrain model with feedback")
    print("  [V] View angle difference history")
    print("  [Q] Quit")
    print("="*70)
    
    while True:
        s = scenarios[current_scenario]
        input_val = np.array([[s['hr'], s['speed'], s['time'], s['mode']]], dtype=np.float32)
        interpreter.set_tensor(in_idx, input_val)
        interpreter.invoke()
        angle = interpreter.get_tensor(out_idx)[0][0]
        m_str = "HIIT" if s['mode'] == 1 else "Long"
        
        print(f"\nScenario {current_scenario + 1}/{len(scenarios)}: {s['desc']}")
        print(f"   HR: {s['hr']} BPM | Speed: {s['speed']:.1f} m/s | Mode: {m_str} | Time: {s['time']}s")
        print(f"   Predicted Servo Angle: {angle:.2f}°")
        
        choice = input("\nAction [N/F/G/V/Q]: ").strip().upper()
        
        #next scenario
        if choice == 'N':
            current_scenario = (current_scenario + 1) % len(scenarios)
            angle_before_retrain = None  # reset when changing scenarios
        
        # feedback
        elif choice == 'F':
            print("\nFeedback options:")
            print("  [1] Resistance is good")
            print("  [2] Resistance is too easy")
            print("  [3] Resistance is too hard")
            feedback_choice = input("Select [1/2/3]: ").strip()
            
            feedback_map = {'1': 'good', '2': 'too_easy', '3': 'too_hard'}
            if feedback_choice in feedback_map:
                save_feedback(
                    heartrate=s['hr'],
                    speed=s['speed'],
                    time_offset=s['time'],
                    mode=s['mode'],
                    current_angle=angle,
                    feedback_type=feedback_map[feedback_choice]
                )
            else:
                print("Invalid feedback choice")
        
        # generate new model based on current feedback 
        elif choice == 'G':
            # store angle before retraining
            angle_before_retrain = angle
            
            retrain_model()
            
            # reload interpreter
            interpreter = tf.lite.Interpreter(model_path="bike_prediction_model.tflite")
            interpreter.allocate_tensors()
            in_idx = interpreter.get_input_details()[0]['index']
            out_idx = interpreter.get_output_details()[0]['index']
            
            # get new prediction for same scenario
            input_val = np.array([[s['hr'], s['speed'], s['time'], s['mode']]], dtype=np.float32)
            interpreter.set_tensor(in_idx, input_val)
            interpreter.invoke()
            angle_after_retrain = interpreter.get_tensor(out_idx)[0][0]
            
            # save the difference
            save_angle_difference(
                scenario_desc=s['desc'],
                hr=s['hr'],
                speed=s['speed'],
                time=s['time'],
                mode=s['mode'],
                before_angle=angle_before_retrain,
                after_angle=angle_after_retrain
            )
            
            print("Model reloaded. Test again to see changes!")
        
        # view angle difference history
        elif choice == 'V':
            if angle_differences:
                print("\n" + "="*70)
                print("ANGLE DIFFERENCE HISTORY")
                print("="*70)
                for i, record in enumerate(angle_differences[-10:], 1):  #last 10 angles
                    print(f"\n{i}. {record['scenario']} ({record['timestamp'][:19]})")
                    print(f"   HR: {record['hr']} | Speed: {record['speed']} | Mode: {record['mode']}")
                    print(f"   {record['angle_before']}° → {record['angle_after']}° | Δ = {record['difference']}°")
                print("="*70)
            else:
                print("\nNo angle differences recorded yet. Retrain model to see changes!")
        
        # quit 
        elif choice == 'Q':
            break
        
        else:
            print("Invalid choice. Use N, F, G, V, or Q")

if __name__ == "__main__":
    run_interactive_test()