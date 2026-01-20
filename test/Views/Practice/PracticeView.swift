//
//  PracticeView.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import SwiftUI
import SwiftData

struct PracticeView: View {
    @State var viewModel: PracticeSessionViewModel
    @Environment(\.modelContext) private var modelContext

    @Query private var pieces: [Piece]
    @State private var showPieceSelection = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 32) {
                // タイマー表示
                TimerDisplay(
                    duration: viewModel.currentSession?.duration ?? 0,
                    isActive: viewModel.isSessionActive
                )

                if !viewModel.isSessionActive {
                    // セッション開始前
                    idleView
                } else {
                    // セッション進行中
                    activeView
                }

                Spacer()
            }
            .padding()
            .navigationTitle("練習")
            .sheet(isPresented: $showPieceSelection) {
                PieceSelectionView(
                    pieces: pieces,
                    selectedPieces: $viewModel.selectedPieces
                )
            }
        }
    }

    private var idleView: some View {
        VStack(spacing: 24) {
            // 曲選択
            VStack(alignment: .leading, spacing: 12) {
                Text("練習する曲を選択")
                    .font(.headline)

                Button {
                    showPieceSelection = true
                } label: {
                    HStack {
                        Image(systemName: "plus.circle.fill")
                        Text("曲を追加")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color(.systemGray6))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }

                if !viewModel.selectedPieces.isEmpty {
                    ForEach(viewModel.selectedPieces) { piece in
                        HStack {
                            Text(piece.title)
                            Spacer()
                            Button {
                                viewModel.removePiece(piece)
                            } label: {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundStyle(.gray)
                            }
                        }
                        .padding()
                        .background(Color(.systemGray6))
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                }
            }

            // 開始ボタン
            Button {
                viewModel.startSession()
            } label: {
                Text("練習を開始")
                    .font(.headline)
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color(red: 91/255, green: 33/255, blue: 182/255))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }
        }
    }

    private var activeView: some View {
        VStack(spacing: 24) {
            // 練習中の曲
            if !viewModel.selectedPieces.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("練習中の曲")
                        .font(.headline)

                    ForEach(viewModel.selectedPieces) { piece in
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundStyle(.green)
                            Text(piece.title)
                            Spacer()
                            Text(piece.difficulty.emoji)
                        }
                        .padding()
                        .background(Color(.systemGray6))
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                }
            }

            // メモ
            VStack(alignment: .leading, spacing: 8) {
                Text("メモ")
                    .font(.headline)

                TextEditor(text: $viewModel.sessionNotes)
                    .frame(height: 100)
                    .padding(8)
                    .background(Color(.systemGray6))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
            }

            // 終了ボタン
            Button {
                viewModel.endSession()
            } label: {
                Text("練習を終了")
                    .font(.headline)
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.red)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }
        }
    }
}

struct TimerDisplay: View {
    let duration: TimeInterval
    let isActive: Bool

    var formattedTime: String {
        let hours = Int(duration) / 3600
        let minutes = Int(duration) / 60 % 60
        let seconds = Int(duration) % 60

        return String(format: "%02d:%02d:%02d", hours, minutes, seconds)
    }

    var body: some View {
        VStack(spacing: 8) {
            if isActive {
                HStack(spacing: 4) {
                    Circle()
                        .fill(.red)
                        .frame(width: 12, height: 12)
                    Text("REC")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundStyle(.red)
                }
            }

            Text(formattedTime)
                .font(.system(size: 56, weight: .bold, design: .monospaced))
                .foregroundStyle(isActive ? .primary : .secondary)
        }
        .frame(height: 200)
    }
}

struct PieceSelectionView: View {
    let pieces: [Piece]
    @Binding var selectedPieces: [Piece]
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List(pieces) { piece in
                Button {
                    if selectedPieces.contains(where: { $0.id == piece.id }) {
                        selectedPieces.removeAll { $0.id == piece.id }
                    } else {
                        selectedPieces.append(piece)
                    }
                } label: {
                    HStack {
                        VStack(alignment: .leading) {
                            Text(piece.title)
                                .font(.headline)
                            if !piece.composer.isEmpty {
                                Text(piece.composer)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        Spacer()
                        if selectedPieces.contains(where: { $0.id == piece.id }) {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundStyle(.green)
                        }
                    }
                }
                .foregroundStyle(.primary)
            }
            .navigationTitle("曲を選択")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("完了") {
                        dismiss()
                    }
                }
            }
        }
    }
}

#Preview {
    PracticeView(
        viewModel: PracticeSessionViewModel(
            repository: PracticeSessionRepository(
                modelContext: ModelContext(.init(for: PracticeSession.self, Piece.self))
            )
        )
    )
    .modelContainer(for: [PracticeSession.self, Piece.self])
}
