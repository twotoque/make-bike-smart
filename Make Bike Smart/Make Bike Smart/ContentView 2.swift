//
//  ContentView 2.swift
//  Make Bike Smart
//
//  Created by Derek Song on 2025-12-30.
//


import SwiftUI
import HealthKit

struct ContentView: View {
    @StateObject var hkManager = HealthKitManager()
    
    @State private var speed: Double = 0.0
    @State private var servoAngle: Double = 0.0
    @State private var workoutMode: String = "Long Distance"
    @State private var debugMode: Bool = false
    @State private var debugHR: Int = 70
    
    // Use either real HR or debug HR
    private var displayHR: Int {
        debugMode ? debugHR : hkManager.currentHR
    }
    
    var body: some View {
        ZStack {
            Color(UIColor.systemBackground).ignoresSafeArea()
            
            VStack(spacing: 30) {
                HStack {
                    VStack(alignment: .leading) {
                        Text("Make Bike Smart")
                            .font(.headline)
                            .bold()
                        Text("Derek Song")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    VStack(alignment: .trailing) {
                        Button(action: { 
                            hkManager.requestAuthorization()
                            debugMode = false  // Exit debug mode when connecting
                        }) {
                            HStack {
                                if hkManager.session != nil {
                                    Image(systemName: "antenna.radiowaves.left.and.right")
                                }
                                Text(hkManager.session != nil ? "Mirroring Live" : "Connect HR")
                            }
                            .font(.caption)
                            .bold()
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(hkManager.session != nil ? .green : .blue)

                        Text(hkManager.statusMessage)
                            .font(.system(size: 8))
                            .foregroundColor(.secondary)
                    }
                }
                .padding(.horizontal)

                // speedometer
                VStack {
                    Text("\(speed, specifier: "%.1f")")
                        .font(.system(size: 80, weight: .bold, design: .rounded))
                    Text("METERS / SEC")
                        .font(.headline)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 40)

                // data
                HStack(spacing: 20) {
                    DataCard(
                        title: "HEART RATE", 
                        value: "\(displayHR)", 
                        unit: debugMode ? "DEBUG" : "BPM", 
                        icon: "heart.fill", 
                        color: debugMode ? .orange : .red
                    )
                    DataCard(
                        title: "SERVO ANGLE", 
                        value: "\(Int(servoAngle))", 
                        unit: "DEGREES", 
                        icon: "gearshape.fill", 
                        color: .blue
                    )
                }
                .padding(.horizontal)

                // mode
                Picker("Workout Mode", selection: $workoutMode) {
                    Text("Long Distance").tag("Long Distance")
                    Text("HIIT").tag("HIIT")
                }
                .pickerStyle(.segmented)
                .padding(.horizontal)

                Spacer()

                // debug
                VStack(spacing: 10) {
                    HStack {
                        Text("DEBUG SIMULATOR")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Toggle("", isOn: $debugMode)
                            .labelsHidden()
                    }
                    
                    if debugMode {
                        HStack {
                            Button("Inc. Speed") { 
                                speed += 0.5
                                updateServo() 
                            }
                            Button("Inc. HR") {
                                debugHR = (debugHR == 0) ? 70 : debugHR + 5
                                updateServo()
                            }
                            Button("Dec. HR") {
                                debugHR = max(debugHR - 5, 40)
                                updateServo()
                            }
                            Button("Reset") {
                                speed = 0
                                debugHR = 70
                                updateServo()
                            }
                        }
                        .buttonStyle(.bordered)
                    }
                }
                .padding()
            }
        }
        .onChange(of: hkManager.currentHR) {
            if !debugMode {
                updateServo()
            }
        }
        .onChange(of: debugHR) {
            if debugMode {
                updateServo()
            }
        }
        .onChange(of: workoutMode) {
            updateServo()
        }
    }
    
    func updateServo() {
        let activeHR = displayHR > 0 ? Double(displayHR) : 70.0
        let predictedWatts = (activeHR - 60) * 1.8
        let multiplier = (workoutMode == "HIIT" ? 1.3 : 1.0)
        
        // Safety: Avoid division by zero
        let denominator = speed + 0.1
        let angle = (predictedWatts / denominator) * 2.2
        
        servoAngle = min(max(angle * multiplier, 0), 180)
    }
}

struct DataCard: View {
    var title: String
    var value: String
    var unit: String
    var icon: String
    var color: Color
    
    var body: some View {
        VStack(alignment: .leading) {
            HStack {
                Image(systemName: icon)
                Text(title)
            }
            .font(.caption2)
            .bold()
            .foregroundColor(color)
            
            Spacer()
            
            HStack(alignment: .bottom, spacing: 4) {
                Text(value)
                    .font(.system(size: 30, weight: .bold, design: .rounded))
                Text(unit)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: 100)
        .background(Color(UIColor.secondarySystemBackground))
        .cornerRadius(15)
    }
}