//
//  Date+Extensions.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import Foundation

extension Date {
    var isToday: Bool {
        Calendar.current.isDateInToday(self)
    }

    var isYesterday: Bool {
        Calendar.current.isDateInYesterday(self)
    }

    func formatted(as style: DateFormatterStyle) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = style
        formatter.timeStyle = .none
        formatter.locale = Locale(identifier: "ja_JP")
        return formatter.string(from: self)
    }

    func timeFormatted() -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .none
        formatter.timeStyle = .short
        formatter.locale = Locale(identifier: "ja_JP")
        return formatter.string(from: self)
    }

    func relativeDateString() -> String {
        if isToday {
            return "今日"
        } else if isYesterday {
            return "昨日"
        } else {
            let calendar = Calendar.current
            let daysAgo = calendar.dateComponents([.day], from: self, to: Date()).day ?? 0
            if daysAgo < 7 {
                return "\(daysAgo)日前"
            } else {
                return formatted(as: .medium)
            }
        }
    }
}
