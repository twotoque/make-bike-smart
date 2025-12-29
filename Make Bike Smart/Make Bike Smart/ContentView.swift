import SwiftUI
import HealthKit

struct ContentView: View {
    // simulated data
    @State private var speed: Double = 0.0
    @State private var heartRate: Int = 0
    @State private var servoAngle: Double = 0.0
    @State private var isConnected: Bool = false
    @State private var workoutMode: String = "Long Distance"
    
    var body: some View {
        ZStack {
            Color(UIColor.systemBackground).ignoresSafeArea()
            
            VStack(spacing: 30) {
                HStack {
                    Text("Make Bike Smart by Derek Song")
                        .font(.system(size: 24))
                    Spacer()
                    Circle()
                        .frame(width: 12, height: 12)
                        .foregroundColor(isConnected ? .green : .red)
                    Text(isConnected ? "CONNECTED" : "DISCONNECTED")
                        .font(.caption2)
                        .bold()
                }
                .padding(.horizontal)

                VStack {
                    Text("\(speed, specifier: "%.1f")")
                        .font(.system(size: 80, weight: .bold, design: .rounded))
                    Text("METERS / SEC")
                        .font(.headline)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 40)

                HStack(spacing: 20) {
                    DataCard(title: "HEART RATE", value: "\(heartRate)", unit: "BPM", icon: "heart.fill", color: .red)
                    DataCard(title: "SERVO ANGLE", value: "\(Int(servoAngle))", unit: "DEGREES", icon: "gearshape.fill", color: .blue)
                }
                .padding(.horizontal)

                Picker("Workout Mode", selection: $workoutMode) {
                    Text("Long Distance").tag("Long Distance")
                    Text("HIIT").tag("HIIT")
                }
                .pickerStyle(.segmented)
                .padding(.horizontal)

                Spacer()

                VStack(spacing: 10) {
                    Text("DEBUG SIMULATOR").font(.caption).foregroundColor(.secondary)
                    HStack {
                        Button("Inc. Speed") { speed += 0.5; updateServo() }
                        Button("Inc. HR") { heartRate += 5; updateServo() }
                        Button("Reset") { speed = 0; heartRate = 70; updateServo() }
                    }
                    .buttonStyle(.bordered)
                }
                .padding()
            }
        }
    }
    
    func updateServo() {
        let predictedWatts = Double(heartRate - 60) * 1.8
        let multiplier = (workoutMode == "HIIT" ? 1.3 : 1.0)
        let angle = (predictedWatts / (speed + 0.1)) * 2.2
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
