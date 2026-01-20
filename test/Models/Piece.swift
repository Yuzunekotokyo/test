//
//  Piece.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import Foundation
import SwiftData

@Model
final class Piece {
    @Attribute(.unique) var id: UUID
    var title: String
    var composer: String
    var difficulty: Difficulty
    var status: PieceStatus
    var tags: [String]
    var notes: String
    var createdAt: Date
    var lastPracticedAt: Date?

    @Relationship(deleteRule: .nullify, inverse: \PracticeSession.pieces)
    var sessions: [PracticeSession]

    init(
        title: String,
        composer: String = "",
        difficulty: Difficulty = .beginner,
        status: PieceStatus = .learning
    ) {
        self.id = UUID()
        self.title = title
        self.composer = composer
        self.difficulty = difficulty
        self.status = status
        self.tags = []
        self.notes = ""
        self.createdAt = Date()
        self.sessions = []
    }

    var totalPracticeTime: TimeInterval {
        sessions.reduce(0) { $0 + $1.duration }
    }

    var sessionCount: Int {
        sessions.count
    }
}
