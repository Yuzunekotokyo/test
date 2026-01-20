//
//  HomeView.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import SwiftUI

struct HomeView: View {
    @State var viewModel: HomeViewModel

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // 今日の練習時間カード
                    TodayProgressCard(
                        practiceTime: viewModel.todayPracticeTime,
                        goal: 3600 // 60分 = 3600秒
                    )

                    // ストリークカード
                    StreakCard(streak: viewModel.practiceStreak)

                    // 総練習時間
                    StatCard(
                        title: "総練習時間",
                        value: StatisticsService.formatTime(viewModel.totalPracticeTime),
                        icon: "clock.fill"
                    )

                    // 最近練習した曲
                    if !viewModel.recentPieces.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("最近練習した曲")
                                .font(.headline)
                                .padding(.horizontal)

                            ForEach(viewModel.recentPieces) { piece in
                                RecentPieceCard(piece: piece)
                            }
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("ホーム")
            .onAppear {
                viewModel.loadData()
            }
        }
    }
}

struct TodayProgressCard: View {
    let practiceTime: TimeInterval
    let goal: TimeInterval

    var progress: Double {
        min(practiceTime / goal, 1.0)
    }

    var body: some View {
        VStack(spacing: 16) {
            Text("今日の練習時間")
                .font(.headline)

            ZStack {
                Circle()
                    .stroke(Color.gray.opacity(0.2), lineWidth: 20)
                    .frame(width: 180, height: 180)

                Circle()
                    .trim(from: 0, to: progress)
                    .stroke(
                        Color(red: 91/255, green: 33/255, blue: 182/255),
                        style: StrokeStyle(lineWidth: 20, lineCap: .round)
                    )
                    .frame(width: 180, height: 180)
                    .rotationEffect(.degrees(-90))

                VStack(spacing: 4) {
                    Text(StatisticsService.formatTime(practiceTime))
                        .font(.title)
                        .fontWeight(.bold)
                    Text("/ \(Int(goal / 60))分")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }

            if progress < 1.0 {
                Text("目標達成まであと\(StatisticsService.formatTime(goal - practiceTime))")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } else {
                Text("目標達成！")
                    .font(.caption)
                    .foregroundStyle(.green)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .shadow(radius: 2)
    }
}

struct StreakCard: View {
    let streak: Int

    var body: some View {
        HStack {
            Image(systemName: "flame.fill")
                .font(.title)
                .foregroundStyle(.orange)

            VStack(alignment: .leading) {
                Text("練習ストリーク")
                    .font(.headline)
                Text("\(streak)日連続")
                    .font(.title2)
                    .fontWeight(.bold)
            }

            Spacer()
        }
        .padding()
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .shadow(radius: 2)
    }
}

struct StatCard: View {
    let title: String
    let value: String
    let icon: String

    var body: some View {
        HStack {
            Image(systemName: icon)
                .font(.title2)
                .foregroundStyle(Color(red: 91/255, green: 33/255, blue: 182/255))

            VStack(alignment: .leading) {
                Text(title)
                    .font(.headline)
                Text(value)
                    .font(.title3)
                    .fontWeight(.semibold)
            }

            Spacer()
        }
        .padding()
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .shadow(radius: 2)
    }
}

struct RecentPieceCard: View {
    let piece: Piece

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(piece.title)
                    .font(.headline)
                if !piece.composer.isEmpty {
                    Text(piece.composer)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                HStack(spacing: 8) {
                    Text(piece.difficulty.emoji)
                    Text(piece.difficulty.rawValue)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 4) {
                if let lastPracticed = piece.lastPracticedAt {
                    Text(lastPracticed.relativeDateString())
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Text(StatisticsService.formatTime(piece.totalPracticeTime))
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(radius: 1)
    }
}

#Preview {
    HomeView(
        viewModel: HomeViewModel(
            sessionRepository: PracticeSessionRepository(modelContext: ModelContext(.init(for: PracticeSession.self, Piece.self))),
            pieceRepository: PieceRepository(modelContext: ModelContext(.init(for: PracticeSession.self, Piece.self)))
        )
    )
}
