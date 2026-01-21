import SwiftUI
import SwiftData

struct HomeView: View {
    @Environment(\.modelContext) private var modelContext
    @State private var viewModel = StudyViewModel()
    @Query private var records: [StudyRecord]

    var currentStreak: Int {
        StreakCalculator.calculateCurrentStreak(from: records)
    }

    var bonusMultiplier: Double {
        StreakCalculator.calculateBonusMultiplier(streak: currentStreak)
    }

    var todayPoints: Int {
        if let todayRecord = todayRecord {
            return todayRecord.pointsEarned
        }
        return 0
    }

    var todayRecord: StudyRecord? {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())
        return records.first { record in
            calendar.isDate(record.date, inSameDayAs: today)
        }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    streakCard

                    studyInputCard

                    todayStatsCard
                }
                .padding()
            }
            .navigationTitle("EnglishTracker")
            .background(Color(.systemGroupedBackground))
        }
    }

    private var streakCard: some View {
        VStack(spacing: 12) {
            HStack {
                Image(systemName: currentStreak > 0 ? "flame.fill" : "flame")
                    .font(.system(size: 40))
                    .foregroundStyle(currentStreak > 0 ? .orange : .gray)

                VStack(alignment: .leading) {
                    Text("連続学習")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    Text("\(currentStreak)日")
                        .font(.system(size: 36, weight: .bold))
                }

                Spacer()

                VStack(alignment: .trailing) {
                    Text("ボーナス")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text("×\(bonusMultiplier, specifier: "%.1f")")
                        .font(.title2)
                        .fontWeight(.semibold)
                        .foregroundStyle(.green)
                }
            }

            if currentStreak >= 3 {
                Text(bonusMessage)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 2)
    }

    private var studyInputCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("今日の学習を記録")
                .font(.headline)

            VStack(spacing: 12) {
                HStack {
                    Text("学習時間")
                        .frame(width: 100, alignment: .leading)
                    TextField("分", text: $viewModel.studyMinutes)
                        .keyboardType(.numberPad)
                        .textFieldStyle(.roundedBorder)
                }

                HStack {
                    Text("学習単語数")
                        .frame(width: 100, alignment: .leading)
                    TextField("単語", text: $viewModel.wordsLearned)
                        .keyboardType(.numberPad)
                        .textFieldStyle(.roundedBorder)
                }

                HStack {
                    Text("問題数")
                        .frame(width: 100, alignment: .leading)
                    TextField("問題", text: $viewModel.problemsSolved)
                        .keyboardType(.numberPad)
                        .textFieldStyle(.roundedBorder)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("メモ")
                    TextField("学習内容のメモ（任意）", text: $viewModel.memo, axis: .vertical)
                        .textFieldStyle(.roundedBorder)
                        .lineLimit(3...6)
                }
            }

            Button(action: {
                viewModel.addStudyRecord(context: modelContext)
            }) {
                Text("記録する")
                    .font(.headline)
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .cornerRadius(12)
            }
            .disabled(viewModel.studyMinutes.isEmpty || Int(viewModel.studyMinutes) == 0)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 2)
    }

    private var todayStatsCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("今日の獲得ポイント")
                .font(.headline)

            HStack {
                Image(systemName: "star.fill")
                    .font(.title)
                    .foregroundStyle(.yellow)

                Text("\(todayPoints)pt")
                    .font(.system(size: 32, weight: .bold))

                Spacer()
            }

            if let record = todayRecord {
                Divider()

                VStack(alignment: .leading, spacing: 8) {
                    statRow(icon: "clock.fill", label: "学習時間", value: "\(record.studyMinutes)分")
                    if record.wordsLearned > 0 {
                        statRow(icon: "book.fill", label: "単語数", value: "\(record.wordsLearned)")
                    }
                    if record.problemsSolved > 0 {
                        statRow(icon: "checkmark.circle.fill", label: "問題数", value: "\(record.problemsSolved)")
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 2)
    }

    private func statRow(icon: String, label: String, value: String) -> some View {
        HStack {
            Image(systemName: icon)
                .foregroundStyle(.blue)
                .frame(width: 24)
            Text(label)
                .foregroundStyle(.secondary)
            Spacer()
            Text(value)
                .fontWeight(.semibold)
        }
        .font(.subheadline)
    }

    private var bonusMessage: String {
        switch currentStreak {
        case 30...:
            return "🎉 素晴らしい！30日連続達成で5倍ボーナス！"
        case 14..<30:
            return "🎊 2週間連続達成で3倍ボーナス！"
        case 7..<14:
            return "⭐️ 1週間連続達成で2倍ボーナス！"
        case 3..<7:
            return "✨ 3日連続達成で1.5倍ボーナス！"
        default:
            return ""
        }
    }
}
