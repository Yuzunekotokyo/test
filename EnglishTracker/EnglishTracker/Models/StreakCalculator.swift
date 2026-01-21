import Foundation

struct StreakCalculator {
    static func calculateCurrentStreak(from records: [StudyRecord]) -> Int {
        guard !records.isEmpty else { return 0 }

        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())

        let sortedRecords = records
            .map { calendar.startOfDay(for: $0.date) }
            .sorted(by: >)

        var currentStreak = 0
        var expectedDate = today

        for recordDate in sortedRecords {
            if calendar.isDate(recordDate, inSameDayAs: expectedDate) {
                currentStreak += 1
                expectedDate = calendar.date(byAdding: .day, value: -1, to: expectedDate) ?? expectedDate
            } else if recordDate < expectedDate {
                break
            }
        }

        return currentStreak
    }

    static func calculateBonusMultiplier(streak: Int) -> Double {
        switch streak {
        case 30...:
            return 5.0
        case 14..<30:
            return 3.0
        case 7..<14:
            return 2.0
        case 3..<7:
            return 1.5
        default:
            return 1.0
        }
    }

    static func calculatePoints(studyMinutes: Int, streak: Int) -> Int {
        let basePoints = studyMinutes
        let multiplier = calculateBonusMultiplier(streak: streak)
        return Int(Double(basePoints) * multiplier)
    }

    static func calculateMaxStreak(from records: [StudyRecord]) -> Int {
        guard !records.isEmpty else { return 0 }

        let calendar = Calendar.current
        let sortedRecords = records
            .map { calendar.startOfDay(for: $0.date) }
            .sorted(by: <)

        var maxStreak = 1
        var currentStreak = 1
        var previousDate = sortedRecords[0]

        for i in 1..<sortedRecords.count {
            let currentDate = sortedRecords[i]
            let daysDifference = calendar.dateComponents([.day], from: previousDate, to: currentDate).day ?? 0

            if daysDifference == 1 {
                currentStreak += 1
                maxStreak = max(maxStreak, currentStreak)
            } else if daysDifference > 1 {
                currentStreak = 1
            }

            previousDate = currentDate
        }

        return maxStreak
    }
}
