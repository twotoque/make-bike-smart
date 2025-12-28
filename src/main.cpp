#include <Arduino.h>
#include <Servo.h>

// define pins 
const int HALL_SENSOR_PIN = 2;  
const int SERVO_PIN = 15;
const int BAUD_RATE = 115200;       

// tracking data 
volatile int totalCycles = 0;
int lastReportedCycles = 0;

// temp control data (to be set by middleware/ML)
int currentResistanceLevel = 0;

Servo resistanceServo;

void countRotation() {
  totalCycles++;
}

void setup() {
  Serial.begin(BAUD_RATE);
  
  pinMode(HALL_SENSOR_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(HALL_SENSOR_PIN), countRotation, FALLING);

  resistanceServo.attach(SERVO_PIN);
  
  //start at lowest resistance
  resistanceServo.write(0);
 }

void loop() {
  
  // -- outbound data
  // send totalCycles to middleware/ML
  if (totalCycles > lastReportedCycles) {
    lastReportedCycles = totalCycles;
    
    // CYCLE COUNT: [lastReportedCycles]
    Serial.print("CYCLE COUNT:"); 
    Serial.println(lastReportedCycles);
  }

  // -- inbound data
  // -- resistance updates set by ml 
  if (Serial.available() > 0) {
    int targetResistance = Serial.parseInt();
    
    if (targetResistance >= 0 && targetResistance <= 180) {
      currentResistanceLevel = targetResistance;
      resistanceServo.write(currentResistanceLevel);
      
      // NEW RESISTANCE: [currentResistanceLevel]
      Serial.print("NEW RESISTANCE:");
      Serial.println(currentResistanceLevel);
    }
  }

  delay(5);
}