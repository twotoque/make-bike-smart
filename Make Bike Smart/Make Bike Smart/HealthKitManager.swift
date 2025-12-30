//
//  HealthKitManager.swift
//  Make Bike Smart
//
//  Created by Derek Song on 2025-12-28.
//
import Foundation
import HealthKit

class HealthKitManager: NSObject, ObservableObject, HKWorkoutSessionDelegate {
    @Published var currentHR: Int = 0
    @Published var isAuthorized = false
    @Published var statusMessage: String = "Idle"
    
    @Published var session: HKWorkoutSession?
    let healthStore = HKHealthStore()
    
    private var heartRateQuery: HKAnchoredObjectQuery?

    override init() {
        super.init()
        setupMirroringHandler()
    }

    private func setupMirroringHandler() {
        healthStore.workoutSessionMirroringStartHandler = { mirroredSession in
            DispatchQueue.main.async {
                self.statusMessage = "Mirroring Started"
                self.session = mirroredSession
                self.session?.delegate = self
                
                self.startHeartRateQuery()
            }
        }
    }

    func requestAuthorization() {
        self.statusMessage = "Requesting..."
        let hrType = HKQuantityType.quantityType(forIdentifier: .heartRate)!
        let typesToRead: Set = [hrType, HKObjectType.workoutType()]
        
        healthStore.requestAuthorization(toShare: nil, read: typesToRead) { success, error in
            DispatchQueue.main.async {
                if let error = error {
                    self.statusMessage = "Error: \(error.localizedDescription)"
                } else if success {
                    self.statusMessage = "Ready for Mirroring"
                    self.isAuthorized = true
                    
                    self.startHeartRateQuery()
                }
            }
        }
    }
    
    private func startHeartRateQuery() {
        if let query = heartRateQuery {
            healthStore.stop(query)
        }
        
        guard let heartRateType = HKQuantityType.quantityType(forIdentifier: .heartRate) else {
            return
        }
        
        // create a predicate for recent samples (last 10 seconds)
        let datePredicate = HKQuery.predicateForSamples(
            withStart: Date().addingTimeInterval(-10),
            end: nil,
            options: .strictStartDate
        )
        
        // create an anchored object query for continuous updates
        heartRateQuery = HKAnchoredObjectQuery(
            type: heartRateType,
            predicate: datePredicate,
            anchor: nil,
            limit: HKObjectQueryNoLimit
        ) { [weak self] query, samples, deletedObjects, anchor, error in
            self?.processHeartRateSamples(samples)
        }
        
        heartRateQuery?.updateHandler = { [weak self] query, samples, deletedObjects, anchor, error in
            self?.processHeartRateSamples(samples)
        }
        
        healthStore.execute(heartRateQuery!)
        
        DispatchQueue.main.async {
            self.statusMessage = "Monitoring HR"
        }
    }
    
    private func processHeartRateSamples(_ samples: [HKSample]?) {
        guard let heartRateSamples = samples as? [HKQuantitySample] else {
            return
        }
        
        guard let sample = heartRateSamples.last else {
            return
        }
        
        let heartRateUnit = HKUnit.count().unitDivided(by: .minute())
        let heartRate = sample.quantity.doubleValue(for: heartRateUnit)
        
        DispatchQueue.main.async {
            self.currentHR = Int(heartRate)
            self.statusMessage = "HR Updated: \(Int(heartRate)) BPM"
        }
    }

    func workoutSession(_ workoutSession: HKWorkoutSession, didChangeTo toState: HKWorkoutSessionState, from fromState: HKWorkoutSessionState, date: Date) {
        DispatchQueue.main.async {
            self.statusMessage = "Session: \(toState.rawValue)"
            
            // start heartrate query when workout becomes active
            if toState == .running {
                self.startHeartRateQuery()
            }
        }
    }

    func workoutSession(_ workoutSession: HKWorkoutSession, didFailWithError error: Error) {
        DispatchQueue.main.async {
            self.statusMessage = "Error: \(error.localizedDescription)"
        }
    }

    func workoutSession(_ workoutSession: HKWorkoutSession, didReceiveDataFromRemoteWorkoutSession data: [Data]) {
        // Handle remote data if needed
    }
    
    deinit {
        if let query = heartRateQuery {
            healthStore.stop(query)
        }
    }
}
