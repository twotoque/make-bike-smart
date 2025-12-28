#include <Servo.h>

// Pin Definitions
const int HALL_SENSOR_PIN = 2;  
const int SERVO_PIN = 15;       

// Variables
// volatile is important here so the CPU always reads the latest value from RAM
volatile int rotationCount = 0;
int lastProcessedCount = 0;
Servo myServo;

// Standard function for Pico interrupts (no IRAM_ATTR needed)
void countRotation() {
  rotationCount++;
}

void setup() {
  Serial.begin(115200);

  pinMode(HALL_SENSOR_PIN, INPUT_PULLUP);
  
  // Attach interrupt
  attachInterrupt(digitalPinToInterrupt(HALL_SENSOR_PIN), countRotation, FALLING);

  myServo.attach(SERVO_PIN);
  myServo.write(0); 
  
  Serial.println("System Initialized. Waiting for rotations...");
}

void loop() {
  if (rotationCount > lastProcessedCount) {
    lastProcessedCount = rotationCount;
    
    Serial.print("Rotation Detected! Total: ");
    Serial.println(lastProcessedCount);

    // Servo Logic
    myServo.write(90);  
    delay(500);         
    myServo.write(0);   
  }
  
  delay(10); 
}