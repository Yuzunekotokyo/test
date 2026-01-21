import Foundation
import SwiftUI

enum CatMilestone {
    case normal        // 0-99pt
    case stretching    // 100-499pt
    case eiffelTower   // 500-999pt
    case mountFuji     // 1000-2999pt
    case space         // 3000+pt

    static func milestone(for points: Int) -> CatMilestone {
        switch points {
        case 0..<100:
            return .normal
        case 100..<500:
            return .stretching
        case 500..<1000:
            return .eiffelTower
        case 1000..<3000:
            return .mountFuji
        default:
            return .space
        }
    }

    var height: CGFloat {
        switch self {
        case .normal:
            return 80
        case .stretching:
            return 150
        case .eiffelTower:
            return 250
        case .mountFuji:
            return 350
        case .space:
            return 450
        }
    }

    var title: String {
        switch self {
        case .normal:
            return "まだまだこれから"
        case .stretching:
            return "ちょっと伸びてきた"
        case .eiffelTower:
            return "エッフェル塔に到達！"
        case .mountFuji:
            return "富士山に到達！"
        case .space:
            return "宇宙まで到達！"
        }
    }

    var emoji: String {
        switch self {
        case .normal:
            return "🐱"
        case .stretching:
            return "😸"
        case .eiffelTower:
            return "🗼"
        case .mountFuji:
            return "🗻"
        case .space:
            return "🚀✨"
        }
    }

    var backgroundColor: Color {
        switch self {
        case .normal:
            return Color.blue.opacity(0.1)
        case .stretching:
            return Color.green.opacity(0.1)
        case .eiffelTower:
            return Color.orange.opacity(0.15)
        case .mountFuji:
            return Color.purple.opacity(0.15)
        case .space:
            return Color.black.opacity(0.8)
        }
    }

    var nextMilestone: Int? {
        switch self {
        case .normal:
            return 100
        case .stretching:
            return 500
        case .eiffelTower:
            return 1000
        case .mountFuji:
            return 3000
        case .space:
            return nil
        }
    }
}
