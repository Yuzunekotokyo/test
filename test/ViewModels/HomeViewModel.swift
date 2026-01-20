//
//  HomeViewModel.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import Foundation
import SwiftData

@MainActor
@Observable
final class HomeViewModel {
    private let sessionRepository: PracticeSessionRepository
    private let pieceRepository: PieceRepository

    var sessions: [PracticeSession] = []
    var pieces: [Piece] = []

    init(sessionRepository: PracticeSessionRepository, pieceRepository: PieceRepository) {
        self.sessionRepository = sessionRepository
        self.pieceRepository = pieceRepository
        loadData()
    }

    func loadData() {
        sessions = sessionRepository.fetchAll()
        pieces = pieceRepository.fetchAll()
    }

    var todayPracticeTime: TimeInterval {
        StatisticsService.practiceTimeForToday(sessions: sessions)
    }

    var weeklyPracticeTime: TimeInterval {
        StatisticsService.practiceTimeForWeek(sessions: sessions)
    }

    var practiceStreak: Int {
        StatisticsService.calculateStreak(sessions: sessions)
    }

    var recentPieces: [Piece] {
        pieces.filter { $0.lastPracticedAt != nil }
            .sorted { ($0.lastPracticedAt ?? .distantPast) > ($1.lastPracticedAt ?? .distantPast) }
            .prefix(3)
            .map { $0 }
    }

    var totalPracticeTime: TimeInterval {
        StatisticsService.totalPracticeTime(for: sessions)
    }
}
