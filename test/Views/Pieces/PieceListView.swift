//
//  PieceListView.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import SwiftUI

struct PieceListView: View {
    @State var viewModel: PieceListViewModel
    @State private var showAddSheet = false

    var body: some View {
        NavigationStack {
            List {
                ForEach(viewModel.filteredPieces) { piece in
                    NavigationLink(destination: PieceDetailView(piece: piece)) {
                        PieceRow(piece: piece)
                    }
                }
                .onDelete { indexSet in
                    for index in indexSet {
                        viewModel.deletePiece(viewModel.filteredPieces[index])
                    }
                }
            }
            .navigationTitle("曲リスト")
            .searchable(text: $viewModel.searchText, prompt: "曲を検索")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showAddSheet = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showAddSheet) {
                AddPieceView(viewModel: viewModel)
            }
            .overlay {
                if viewModel.pieces.isEmpty {
                    ContentUnavailableView(
                        "曲がありません",
                        systemImage: "music.note.list",
                        description: Text("＋ボタンから曲を追加してください")
                    )
                } else if viewModel.filteredPieces.isEmpty {
                    ContentUnavailableView.search
                }
            }
        }
    }
}

struct PieceRow: View {
    let piece: Piece

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(piece.title)
                    .font(.headline)
                Spacer()
                Text(piece.difficulty.emoji)
                Text(piece.status.emoji)
            }

            if !piece.composer.isEmpty {
                Text(piece.composer)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            HStack(spacing: 16) {
                Label(
                    StatisticsService.formatTime(piece.totalPracticeTime),
                    systemImage: "clock.fill"
                )
                .font(.caption)
                .foregroundStyle(.secondary)

                if let lastPracticed = piece.lastPracticedAt {
                    Label(
                        lastPracticed.relativeDateString(),
                        systemImage: "calendar"
                    )
                    .font(.caption)
                    .foregroundStyle(.secondary)
                }
            }
        }
        .padding(.vertical, 4)
    }
}

struct AddPieceView: View {
    @State var viewModel: PieceListViewModel
    @Environment(\.dismiss) private var dismiss

    @State private var title = ""
    @State private var composer = ""
    @State private var difficulty: Difficulty = .beginner

    var body: some View {
        NavigationStack {
            Form {
                Section("曲の情報") {
                    TextField("曲名", text: $title)
                    TextField("作曲者（任意）", text: $composer)
                }

                Section("難易度") {
                    Picker("難易度", selection: $difficulty) {
                        ForEach(Difficulty.allCases, id: \.self) { level in
                            HStack {
                                Text(level.emoji)
                                Text(level.rawValue)
                            }
                            .tag(level)
                        }
                    }
                    .pickerStyle(.segmented)
                }
            }
            .navigationTitle("新しい曲")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("キャンセル") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("追加") {
                        viewModel.addPiece(
                            title: title,
                            composer: composer,
                            difficulty: difficulty
                        )
                        dismiss()
                    }
                    .disabled(title.isEmpty)
                }
            }
        }
    }
}

struct PieceDetailView: View {
    let piece: Piece

    var body: some View {
        List {
            Section("基本情報") {
                LabeledContent("曲名", value: piece.title)
                if !piece.composer.isEmpty {
                    LabeledContent("作曲者", value: piece.composer)
                }
                LabeledContent("難易度") {
                    HStack {
                        Text(piece.difficulty.emoji)
                        Text(piece.difficulty.rawValue)
                    }
                }
                LabeledContent("ステータス") {
                    HStack {
                        Text(piece.status.emoji)
                        Text(piece.status.rawValue)
                    }
                }
            }

            Section("統計") {
                LabeledContent("累計練習時間") {
                    Text(StatisticsService.formatTime(piece.totalPracticeTime))
                }
                LabeledContent("セッション数") {
                    Text("\(piece.sessionCount)回")
                }
                if let lastPracticed = piece.lastPracticedAt {
                    LabeledContent("最終練習") {
                        Text(lastPracticed.relativeDateString())
                    }
                }
                LabeledContent("追加日") {
                    Text(piece.createdAt.formatted(as: .medium))
                }
            }

            if !piece.notes.isEmpty {
                Section("メモ") {
                    Text(piece.notes)
                }
            }
        }
        .navigationTitle(piece.title)
        .navigationBarTitleDisplayMode(.inline)
    }
}

#Preview {
    PieceListView(
        viewModel: PieceListViewModel(
            repository: PieceRepository(
                modelContext: ModelContext(.init(for: Piece.self, PracticeSession.self))
            )
        )
    )
}
