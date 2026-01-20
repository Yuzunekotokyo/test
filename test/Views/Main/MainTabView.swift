//
//  MainTabView.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import SwiftUI
import SwiftData

struct MainTabView: View {
    @Environment(\.modelContext) private var modelContext

    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView(
                viewModel: HomeViewModel(
                    sessionRepository: PracticeSessionRepository(modelContext: modelContext),
                    pieceRepository: PieceRepository(modelContext: modelContext)
                )
            )
            .tabItem {
                Label("ホーム", systemImage: "house.fill")
            }
            .tag(0)

            PracticeView(
                viewModel: PracticeSessionViewModel(
                    repository: PracticeSessionRepository(modelContext: modelContext)
                )
            )
            .tabItem {
                Label("練習", systemImage: "music.note")
            }
            .tag(1)

            HistoryView()
            .tabItem {
                Label("履歴", systemImage: "chart.bar.fill")
            }
            .tag(2)

            PieceListView(
                viewModel: PieceListViewModel(
                    repository: PieceRepository(modelContext: modelContext)
                )
            )
            .tabItem {
                Label("曲リスト", systemImage: "music.note.list")
            }
            .tag(3)

            SettingsView()
            .tabItem {
                Label("設定", systemImage: "gearshape.fill")
            }
            .tag(4)
        }
        .tint(Color(red: 91/255, green: 33/255, blue: 182/255))
    }
}

#Preview {
    MainTabView()
        .modelContainer(for: [PracticeSession.self, Piece.self])
}
