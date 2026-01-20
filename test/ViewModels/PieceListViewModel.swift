//
//  PieceListViewModel.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import Foundation
import SwiftData

@MainActor
@Observable
final class PieceListViewModel {
    private let repository: PieceRepository

    var pieces: [Piece] = []
    var searchText: String = ""
    var selectedStatus: PieceStatus?

    init(repository: PieceRepository) {
        self.repository = repository
        loadPieces()
    }

    func loadPieces() {
        pieces = repository.fetchAll()
    }

    var filteredPieces: [Piece] {
        var result = pieces

        if !searchText.isEmpty {
            result = result.filter { piece in
                piece.title.localizedCaseInsensitiveContains(searchText) ||
                piece.composer.localizedCaseInsensitiveContains(searchText)
            }
        }

        if let status = selectedStatus {
            result = result.filter { $0.status == status }
        }

        return result
    }

    func addPiece(title: String, composer: String, difficulty: Difficulty) {
        let piece = Piece(title: title, composer: composer, difficulty: difficulty)
        do {
            try repository.save(piece)
            loadPieces()
        } catch {
            print("Failed to save piece: \(error)")
        }
    }

    func deletePiece(_ piece: Piece) {
        do {
            try repository.delete(piece)
            loadPieces()
        } catch {
            print("Failed to delete piece: \(error)")
        }
    }
}
