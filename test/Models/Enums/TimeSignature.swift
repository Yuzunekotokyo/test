//
//  TimeSignature.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import Foundation

enum TimeSignature: String, Codable, CaseIterable {
    case twoFour = "2/4"
    case threeFour = "3/4"
    case fourFour = "4/4"
    case fiveFour = "5/4"
    case sixEight = "6/8"

    var beatsPerMeasure: Int {
        switch self {
        case .twoFour: return 2
        case .threeFour: return 3
        case .fourFour: return 4
        case .fiveFour: return 5
        case .sixEight: return 6
        }
    }
}
