//
//  PracticeSession.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import Foundation
import SwiftData

@Model
final class PracticeSession {
    @Attribute(.unique) var id: UUID
    var startTime: Date
    var endTime: Date?
    var notes: String
    var tempo: Int?
    var createdAt: Date

    @Relationship(deleteRule: .nullify)
    var pieces: [Piece]

    init(startTime: Date = Date()) {
        self.id = UUID()
        self.startTime = startTime
        self.notes = ""
        self.createdAt = Date()
        self.pieces = []
    }

    var duration: TimeInterval {
        guard let endTime = endTime else {
            return Date().timeIntervalSince(startTime)
        }
        return endTime.timeIntervalSince(startTime)
    }

    var isActive: Bool {
        endTime == nil
    }

    var formattedDuration: String {
        let hours = Int(duration) / 3600
        let minutes = Int(duration) / 60 % 60
        let seconds = Int(duration) % 60

        if hours > 0 {
            return String(format: "%02d:%02d:%02d", hours, minutes, seconds)
        } else {
            return String(format: "%02d:%02d", minutes, seconds)
        }
    }
}
