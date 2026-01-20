//
//  Difficulty.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import Foundation

enum Difficulty: String, Codable, CaseIterable {
    case beginner = "初級"
    case intermediate = "中級"
    case advanced = "上級"

    var emoji: String {
        switch self {
        case .beginner: return "🟢"
        case .intermediate: return "🟡"
        case .advanced: return "🔴"
        }
    }
}
