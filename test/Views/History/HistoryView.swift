//
//  HistoryView.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import SwiftUI
import SwiftData

struct HistoryView: View {
    @Query(sort: \PracticeSession.startTime, order: .reverse)
    private var sessions: [PracticeSession]

    var body: some View {
        NavigationStack {
            List {
                if sessions.isEmpty {
                    ContentUnavailableView(
                        "練習履歴がありません",
                        systemImage: "chart.bar",
                        description: Text("練習を開始すると、ここに履歴が表示されます")
                    )
                } else {
                    ForEach(groupedSessions.keys.sorted(by: >), id: \.self) { date in
                        Section(header: Text(formatSectionHeader(date))) {
                            ForEach(groupedSessions[date] ?? []) { session in
                                SessionRow(session: session)
                            }
                        }
                    }
                }
            }
            .navigationTitle("履歴")
        }
    }

    private var groupedSessions: [Date: [PracticeSession]] {
        Dictionary(grouping: sessions) { session in
            Calendar.current.startOfDay(for: session.startTime)
        }
    }

    private func formatSectionHeader(_ date: Date) -> String {
        if date.isToday {
            return "今日"
        } else if date.isYesterday {
            return "昨日"
        } else {
            return date.formatted(as: .medium)
        }
    }
}

struct SessionRow: View {
    let session: PracticeSession

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(session.startTime.timeFormatted())
                    .font(.headline)

                if let endTime = session.endTime {
                    Text("-")
                    Text(endTime.timeFormatted())
                        .font(.headline)
                }

                Spacer()

                Text(session.formattedDuration)
                    .font(.headline)
                    .foregroundStyle(Color(red: 91/255, green: 33/255, blue: 182/255))
            }

            if !session.pieces.isEmpty {
                HStack(spacing: 8) {
                    Image(systemName: "music.note")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Text(session.pieces.map { $0.title }.joined(separator: ", "))
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }

            if !session.notes.isEmpty {
                Text(session.notes)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    HistoryView()
        .modelContainer(for: [PracticeSession.self, Piece.self])
}
