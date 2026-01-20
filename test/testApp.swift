//
//  testApp.swift
//  test
//
//  Created by Kei Tsukamoto  on 2026/01/21.
//

import SwiftUI
import SwiftData

@main
struct testApp: App {
    let modelContainer: ModelContainer

    init() {
        do {
            modelContainer = try ModelContainer(
                for: PracticeSession.self, Piece.self
            )
        } catch {
            fatalError("Failed to initialize ModelContainer: \(error)")
        }
    }

    var body: some Scene {
        WindowGroup {
            MainTabView()
                .modelContainer(modelContainer)
        }
    }
}
