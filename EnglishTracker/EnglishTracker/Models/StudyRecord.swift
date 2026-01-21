import Foundation
import SwiftData

@Model
final class StudyRecord {
    var id: UUID
    var date: Date
    var studyMinutes: Int
    var memo: String
    var wordsLearned: Int
    var problemsSolved: Int
    var pointsEarned: Int

    init(date: Date, studyMinutes: Int, memo: String = "", wordsLearned: Int = 0, problemsSolved: Int = 0, pointsEarned: Int = 0) {
        self.id = UUID()
        self.date = date
        self.studyMinutes = studyMinutes
        self.memo = memo
        self.wordsLearned = wordsLearned
        self.problemsSolved = problemsSolved
        self.pointsEarned = pointsEarned
    }

    var dateOnly: Date {
        Calendar.current.startOfDay(for: date)
    }
}
