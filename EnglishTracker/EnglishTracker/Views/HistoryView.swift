import SwiftUI
import SwiftData

struct HistoryView: View {
    @Query(sort: \StudyRecord.date, order: .reverse) private var records: [StudyRecord]
    @State private var selectedMonth = Date()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    calendarView

                    recordsList
                }
                .padding()
            }
            .navigationTitle("学習履歴")
            .background(Color(.systemGroupedBackground))
        }
    }

    private var calendarView: some View {
        VStack(spacing: 16) {
            HStack {
                Button(action: {
                    selectedMonth = Calendar.current.date(byAdding: .month, value: -1, to: selectedMonth) ?? selectedMonth
                }) {
                    Image(systemName: "chevron.left")
                        .foregroundStyle(.blue)
                }

                Spacer()

                Text(selectedMonth, format: .dateTime.year().month(.wide))
                    .font(.headline)

                Spacer()

                Button(action: {
                    selectedMonth = Calendar.current.date(byAdding: .month, value: 1, to: selectedMonth) ?? selectedMonth
                }) {
                    Image(systemName: "chevron.right")
                        .foregroundStyle(.blue)
                }
            }
            .padding(.horizontal)

            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 7), spacing: 8) {
                ForEach(["日", "月", "火", "水", "木", "金", "土"], id: \.self) { day in
                    Text(day)
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundStyle(.secondary)
                }

                ForEach(daysInMonth, id: \.self) { date in
                    if let date = date {
                        DayCell(date: date, hasRecord: hasRecordForDate(date))
                    } else {
                        Color.clear
                            .frame(height: 40)
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 2)
    }

    private var recordsList: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("最近の記録")
                .font(.headline)
                .padding(.horizontal)

            if records.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "book.closed")
                        .font(.system(size: 48))
                        .foregroundStyle(.gray)
                    Text("学習記録がありません")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 40)
                .background(Color(.systemBackground))
                .cornerRadius(16)
            } else {
                ForEach(records.prefix(20)) { record in
                    RecordRow(record: record)
                }
            }
        }
    }

    private var daysInMonth: [Date?] {
        let calendar = Calendar.current
        let interval = calendar.dateInterval(of: .month, for: selectedMonth)!
        let firstWeekday = calendar.component(.weekday, from: interval.start)
        let numberOfDays = calendar.dateComponents([.day], from: interval.start, to: interval.end).day!

        var days: [Date?] = Array(repeating: nil, count: firstWeekday - 1)

        for day in 0..<numberOfDays {
            if let date = calendar.date(byAdding: .day, value: day, to: interval.start) {
                days.append(date)
            }
        }

        return days
    }

    private func hasRecordForDate(_ date: Date) -> Bool {
        let calendar = Calendar.current
        return records.contains { record in
            calendar.isDate(record.date, inSameDayAs: date)
        }
    }
}

struct DayCell: View {
    let date: Date
    let hasRecord: Bool

    var isToday: Bool {
        Calendar.current.isDateInToday(date)
    }

    var body: some View {
        VStack {
            Text(date, format: .dateTime.day())
                .font(.subheadline)
                .foregroundStyle(isToday ? .white : .primary)
                .frame(width: 40, height: 40)
                .background(
                    Circle()
                        .fill(isToday ? Color.blue : hasRecord ? Color.green.opacity(0.2) : Color.clear)
                )
                .overlay(
                    Circle()
                        .strokeBorder(hasRecord && !isToday ? Color.green : Color.clear, lineWidth: 2)
                )
        }
    }
}

struct RecordRow: View {
    let record: StudyRecord

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(record.date, format: .dateTime.year().month().day())
                    .font(.headline)

                Spacer()

                HStack(spacing: 4) {
                    Image(systemName: "star.fill")
                        .foregroundStyle(.yellow)
                        .font(.caption)
                    Text("\(record.pointsEarned)pt")
                        .font(.subheadline)
                        .fontWeight(.semibold)
                }
            }

            HStack(spacing: 16) {
                Label("\(record.studyMinutes)分", systemImage: "clock.fill")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                if record.wordsLearned > 0 {
                    Label("\(record.wordsLearned)単語", systemImage: "book.fill")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                if record.problemsSolved > 0 {
                    Label("\(record.problemsSolved)問", systemImage: "checkmark.circle.fill")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            if !record.memo.isEmpty {
                Text(record.memo)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.05), radius: 4, x: 0, y: 1)
    }
}
