import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            HomeView()
                .tabItem {
                    Label("ホーム", systemImage: "house.fill")
                }

            HistoryView()
                .tabItem {
                    Label("履歴", systemImage: "calendar")
                }

            StatsView()
                .tabItem {
                    Label("統計", systemImage: "chart.bar.fill")
                }
        }
    }
}
