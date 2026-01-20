//
//  SettingsView.swift
//  test
//
//  Created by Claude on 2026/01/21.
//

import SwiftUI

struct SettingsView: View {
    var body: some View {
        NavigationStack {
            List {
                Section("アプリについて") {
                    LabeledContent("バージョン", value: "1.0.0")
                    LabeledContent("ビルド", value: "1")
                }

                Section {
                    Link(destination: URL(string: "https://github.com")!) {
                        Label("GitHub", systemImage: "link")
                    }
                }
            }
            .navigationTitle("設定")
        }
    }
}

#Preview {
    SettingsView()
}
