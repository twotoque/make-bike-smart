//
//  HealthKitManager.swift
//  Make Bike Smart
//
//  Created by Derek Song on 2025-12-28.
//
import Foundation
import HealthKit

class HealthKitManager: ObservableObject {
    @Published var currentHR: Int = 0
    @Published var isAuthorized = false
    let healthStore = HKHealthStore()

    func requestAuthorization() {
        let hrType = HKQuantityType.quantityType(forIdentifier: .heartRate)!
        healthStore.requestAuthorization(toShare: nil, read: [hrType]) { success, _ in
            if success { self.startHeartRateQuery() }
        }
    }

    func startHeartRateQuery() {
        let hrType = HKQuantityType.quantityType(forIdentifier: .heartRate)!
        let query = HKAnchoredObjectQuery(type: hrType, predicate: nil, anchor: nil, limit: HKObjectQueryNoLimit) { _, samples, _, _, _ in
            self.update(samples)
        }
        query.updateHandler = { _, samples, _, _, _ in self.update(samples) }
        healthStore.execute(query)
    }

    private func update(_ samples: [HKSample]?) {
        guard let sample = samples?.last as? HKQuantitySample else { return }
        DispatchQueue.main.async {
            self.currentHR = Int(sample.quantity.doubleValue(for: HKUnit(from: "count/min")))
        }
    }
}
