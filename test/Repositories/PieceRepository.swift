//
//  PieceRepository.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import Foundation
import SwiftData

@MainActor
final class PieceRepository {
    private let modelContext: ModelContext

    init(modelContext: ModelContext) {
        self.modelContext = modelContext
    }

    func fetchAll() -> [Piece] {
        let descriptor = FetchDescriptor<Piece>(
            sortBy: [SortDescriptor(\.lastPracticedAt, order: .reverse)]
        )
        return (try? modelContext.fetch(descriptor)) ?? []
    }

    func save(_ piece: Piece) throws {
        modelContext.insert(piece)
        try modelContext.save()
    }

    func delete(_ piece: Piece) throws {
        modelContext.delete(piece)
        try modelContext.save()
    }
}
