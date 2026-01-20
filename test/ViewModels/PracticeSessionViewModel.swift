//
//  PracticeSessionViewModel.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import Foundation
import SwiftData

@MainActor
@Observable
final class PracticeSessionViewModel {
    private let repository: PracticeSessionRepository

    var currentSession: PracticeSession?
    var isSessionActive: Bool = false
    var selectedPieces: [Piece] = []
    var sessionNotes: String = ""
    var timer: Timer?

    init(repository: PracticeSessionRepository) {
        self.repository = repository
    }

    func startSession() {
        let session = PracticeSession()
        session.pieces = selectedPieces
        currentSession = session
        isSessionActive = true

        // タイマーを開始（UI更新用）
        timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            self?.objectWillChange.send()
        }
    }

    func endSession() {
        timer?.invalidate()
        timer = nil

        guard let session = currentSession else { return }
        session.endTime = Date()
        session.notes = sessionNotes

        // 曲の最終練習日を更新
        for piece in session.pieces {
            piece.lastPracticedAt = Date()
        }

        do {
            try repository.save(session)
            resetSession()
        } catch {
            print("Failed to save session: \(error)")
        }
    }

    private func resetSession() {
        currentSession = nil
        isSessionActive = false
        selectedPieces = []
        sessionNotes = ""
    }

    func addPiece(_ piece: Piece) {
        if !selectedPieces.contains(where: { $0.id == piece.id }) {
            selectedPieces.append(piece)
        }
    }

    func removePiece(_ piece: Piece) {
        selectedPieces.removeAll { $0.id == piece.id }
    }
}
