A side project to experiment with Rust and its relations with an ESP32 microcontroller with the hope to make my bike smarter (resistance depending on my past Strava rides and map geography)! 


## Hardware
- ESP32
- Input* (aimming for hall effect sensor, simulated with slide switch in Wokwi) → GPIO 4
- Servo motor → GPIO 18
- Status LED → GPIO 2

## How to build 

You must use toolchain version 1.82.0.1 or earlier for compatibility with these HAL versions.

```
cargo install espup

espup install --toolchain-version 1.82.0.1

```

Build using ``` cargo +esp build``` 