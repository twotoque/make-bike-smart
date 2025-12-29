import pandas as pd
import numpy as np
import tensorflow as tf

def run_test():
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
    
    print(f"\n{'Scenario':<22} | {'HR':<5} | {'Speed':<5} | {'Mode':<6} | {'Servo Angle'}")
    print("-" * 65)
    for s in scenarios:
        input_val = np.array([[s['hr'], s['speed'], s['time'], s['mode']]], dtype=np.float32)
        interpreter.set_tensor(in_idx, input_val)
        interpreter.invoke()
        angle = interpreter.get_tensor(out_idx)[0][0]
        m_str = "HIIT" if s['mode'] == 1 else "Long"
        print(f"{s['desc']:<22} | {s['hr']:<5} | {s['speed']:<5.1f} | {m_str:<6} | {angle:.2f}°")

run_test()