//
//  PieceStatus.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import Foundation

enum PieceStatus: String, Codable, CaseIterable {
    case learning = "練習中"
    case reviewing = "復習中"
    case mastered = "マスター済み"
    case paused = "保留中"

    var emoji: String {
        switch self {
        case .learning: return "📚"
        case .reviewing: return "🔄"
        case .mastered: return "✅"
        case .paused: return "⏸️"
        }
    }
}
