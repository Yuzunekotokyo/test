//
//  PracticeSessionRepository.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import Foundation
import SwiftData

@MainActor
final class PracticeSessionRepository {
    private let modelContext: ModelContext

    init(modelContext: ModelContext) {
        self.modelContext = modelContext
    }

    func fetchAll() -> [PracticeSession] {
        let descriptor = FetchDescriptor<PracticeSession>(
            sortBy: [SortDescriptor(\.startTime, order: .reverse)]
        )
        return (try? modelContext.fetch(descriptor)) ?? []
    }

    func fetchSessions(from startDate: Date, to endDate: Date) -> [PracticeSession] {
        let predicate = #Predicate<PracticeSession> { session in
            session.startTime >= startDate && session.startTime <= endDate
        }
        let descriptor = FetchDescriptor(
            predicate: predicate,
            sortBy: [SortDescriptor(\.startTime, order: .reverse)]
        )
        return (try? modelContext.fetch(descriptor)) ?? []
    }

    func save(_ session: PracticeSession) throws {
        modelContext.insert(session)
        try modelContext.save()
    }

    func delete(_ session: PracticeSession) throws {
        modelContext.delete(session)
        try modelContext.save()
    }
}
