import Foundation
import SwiftData
import SwiftUI

@Observable
class StudyViewModel {
    var studyMinutes: String = ""
    var memo: String = ""
    var wordsLearned: String = ""
    var problemsSolved: String = ""

    func addStudyRecord(context: ModelContext) {
        let minutes = Int(studyMinutes) ?? 0
        let words = Int(wordsLearned) ?? 0
        let problems = Int(problemsSolved) ?? 0

        guard minutes > 0 else { return }

        let descriptor = FetchDescriptor<StudyRecord>()
        let allRecords = (try? context.fetch(descriptor)) ?? []

        let currentStreak = StreakCalculator.calculateCurrentStreak(from: allRecords)
        let points = StreakCalculator.calculatePoints(studyMinutes: minutes, streak: currentStreak + 1)

        let record = StudyRecord(
            date: Date(),
            studyMinutes: minutes,
            memo: memo,
            wordsLearned: words,
            problemsSolved: problems,
            pointsEarned: points
        )

        context.insert(record)
        try? context.save()

        studyMinutes = ""
        memo = ""
        wordsLearned = ""
        problemsSolved = ""
    }

    func getTodayRecord(context: ModelContext) -> StudyRecord? {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())

        let descriptor = FetchDescriptor<StudyRecord>()
        let allRecords = (try? context.fetch(descriptor)) ?? []

        return allRecords.first { record in
            calendar.isDate(record.date, inSameDayAs: today)
        }
    }

    func getCurrentStreak(context: ModelContext) -> Int {
        let descriptor = FetchDescriptor<StudyRecord>()
        let allRecords = (try? context.fetch(descriptor)) ?? []
        return StreakCalculator.calculateCurrentStreak(from: allRecords)
    }

    func getTotalPoints(context: ModelContext) -> Int {
        let descriptor = FetchDescriptor<StudyRecord>()
        let allRecords = (try? context.fetch(descriptor)) ?? []
        return allRecords.reduce(0) { $0 + $1.pointsEarned }
    }

    func getTotalStudyMinutes(context: ModelContext) -> Int {
        let descriptor = FetchDescriptor<StudyRecord>()
        let allRecords = (try? context.fetch(descriptor)) ?? []
        return allRecords.reduce(0) { $0 + $1.studyMinutes }
    }

    func getMaxStreak(context: ModelContext) -> Int {
        let descriptor = FetchDescriptor<StudyRecord>()
        let allRecords = (try? context.fetch(descriptor)) ?? []
        return StreakCalculator.calculateMaxStreak(from: allRecords)
    }

    func getBonusMultiplier(context: ModelContext) -> Double {
        let streak = getCurrentStreak(context: context)
        return StreakCalculator.calculateBonusMultiplier(streak: streak)
    }
}
