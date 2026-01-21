import SwiftUI
import SwiftData

struct StatsView: View {
    @Query private var records: [StudyRecord]

    var totalStudyMinutes: Int {
        records.reduce(0) { $0 + $1.studyMinutes }
    }

    var totalPoints: Int {
        records.reduce(0) { $0 + $1.pointsEarned }
    }

    var maxStreak: Int {
        StreakCalculator.calculateMaxStreak(from: records)
    }

    var currentStreak: Int {
        StreakCalculator.calculateCurrentStreak(from: records)
    }

    var totalWords: Int {
        records.reduce(0) { $0 + $1.wordsLearned }
    }

    var totalProblems: Int {
        records.reduce(0) { $0 + $1.problemsSolved }
    }

    var totalDays: Int {
        let calendar = Calendar.current
        let uniqueDates = Set(records.map { calendar.startOfDay(for: $0.date) })
        return uniqueDates.count
    }

    var averageMinutesPerDay: Int {
        guard totalDays > 0 else { return 0 }
        return totalStudyMinutes / totalDays
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    overallStatsCard

                    streakStatsCard

                    learningStatsCard

                    achievementsCard
                }
                .padding()
            }
            .navigationTitle("統計")
            .background(Color(.systemGroupedBackground))
        }
    }

    private var overallStatsCard: some View {
        VStack(spacing: 16) {
            Text("総合統計")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
                StatBox(
                    title: "累計学習時間",
                    value: formatTime(totalStudyMinutes),
                    icon: "clock.fill",
                    color: .blue
                )

                StatBox(
                    title: "累計ポイント",
                    value: "\(totalPoints)pt",
                    icon: "star.fill",
                    color: .yellow
                )

                StatBox(
                    title: "学習日数",
                    value: "\(totalDays)日",
                    icon: "calendar.badge.checkmark",
                    color: .green
                )

                StatBox(
                    title: "1日平均",
                    value: "\(averageMinutesPerDay)分",
                    icon: "chart.bar.fill",
                    color: .purple
                )
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 2)
    }

    private var streakStatsCard: some View {
        VStack(spacing: 16) {
            Text("ストリーク")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            HStack(spacing: 16) {
                VStack(spacing: 8) {
                    Image(systemName: "flame.fill")
                        .font(.system(size: 40))
                        .foregroundStyle(.orange)

                    Text("現在")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Text("\(currentStreak)日")
                        .font(.title2)
                        .fontWeight(.bold)
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color(.secondarySystemBackground))
                .cornerRadius(12)

                VStack(spacing: 8) {
                    Image(systemName: "trophy.fill")
                        .font(.system(size: 40))
                        .foregroundStyle(.yellow)

                    Text("最長記録")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Text("\(maxStreak)日")
                        .font(.title2)
                        .fontWeight(.bold)
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color(.secondarySystemBackground))
                .cornerRadius(12)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 2)
    }

    private var learningStatsCard: some View {
        VStack(spacing: 16) {
            Text("学習内容")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            VStack(spacing: 12) {
                HStack {
                    Image(systemName: "book.fill")
                        .foregroundStyle(.blue)
                        .frame(width: 30)

                    Text("学習単語数")
                        .foregroundStyle(.secondary)

                    Spacer()

                    Text("\(totalWords)")
                        .font(.title3)
                        .fontWeight(.semibold)
                }

                Divider()

                HStack {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                        .frame(width: 30)

                    Text("解いた問題数")
                        .foregroundStyle(.secondary)

                    Spacer()

                    Text("\(totalProblems)")
                        .font(.title3)
                        .fontWeight(.semibold)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 2)
    }

    private var achievementsCard: some View {
        VStack(spacing: 16) {
            Text("達成バッジ")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                AchievementBadge(
                    title: "3日連続",
                    icon: "3.circle.fill",
                    isUnlocked: maxStreak >= 3,
                    color: .blue
                )

                AchievementBadge(
                    title: "7日連続",
                    icon: "7.circle.fill",
                    isUnlocked: maxStreak >= 7,
                    color: .green
                )

                AchievementBadge(
                    title: "14日連続",
                    icon: "14.circle.fill",
                    isUnlocked: maxStreak >= 14,
                    color: .orange
                )

                AchievementBadge(
                    title: "30日連続",
                    icon: "30.circle.fill",
                    isUnlocked: maxStreak >= 30,
                    color: .purple
                )
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 2)
    }

    private func formatTime(_ minutes: Int) -> String {
        let hours = minutes / 60
        let mins = minutes % 60

        if hours > 0 {
            return "\(hours)時間\(mins)分"
        } else {
            return "\(mins)分"
        }
    }
}

struct StatBox: View {
    let title: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundStyle(color)

            Text(value)
                .font(.title3)
                .fontWeight(.bold)

            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(.secondarySystemBackground))
        .cornerRadius(12)
    }
}

struct AchievementBadge: View {
    let title: String
    let icon: String
    let isUnlocked: Bool
    let color: Color

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 40))
                .foregroundStyle(isUnlocked ? color : .gray.opacity(0.3))

            Text(title)
                .font(.caption)
                .foregroundStyle(isUnlocked ? .primary : .secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(.secondarySystemBackground))
        .cornerRadius(12)
        .opacity(isUnlocked ? 1.0 : 0.5)
    }
}
