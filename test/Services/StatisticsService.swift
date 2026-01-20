//
//  StatisticsService.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import Foundation

struct StatisticsService {
    // MARK: - Total Practice Time
    static func totalPracticeTime(for sessions: [PracticeSession]) -> TimeInterval {
        sessions.reduce(0) { $0 + $1.duration }
    }

    // MARK: - Daily Statistics
    static func practiceTimeForToday(sessions: [PracticeSession]) -> TimeInterval {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())
        let tomorrow = calendar.date(byAdding: .day, value: 1, to: today)!

        let todaySessions = sessions.filter { session in
            session.startTime >= today && session.startTime < tomorrow
        }

        return totalPracticeTime(for: todaySessions)
    }

    // MARK: - Weekly Statistics
    static func practiceTimeForWeek(sessions: [PracticeSession]) -> TimeInterval {
        let calendar = Calendar.current
        let now = Date()
        let weekStart = calendar.dateInterval(of: .weekOfYear, for: now)?.start ?? now

        let weekSessions = sessions.filter { $0.startTime >= weekStart }
        return totalPracticeTime(for: weekSessions)
    }

    // MARK: - Streak Calculation
    static func calculateStreak(sessions: [PracticeSession]) -> Int {
        let calendar = Calendar.current
        var streak = 0
        var currentDate = calendar.startOfDay(for: Date())

        let sessionsByDate = Dictionary(grouping: sessions) { session in
            calendar.startOfDay(for: session.startTime)
        }

        while sessionsByDate[currentDate] != nil {
            streak += 1
            guard let previousDay = calendar.date(byAdding: .day, value: -1, to: currentDate) else {
                break
            }
            currentDate = previousDay
        }

        return streak
    }

    // MARK: - Format Time
    static func formatTime(_ timeInterval: TimeInterval) -> String {
        let hours = Int(timeInterval) / 3600
        let minutes = Int(timeInterval) / 60 % 60

        if hours > 0 {
            return "\(hours)時間\(minutes)分"
        } else {
            return "\(minutes)分"
        }
    }
}
