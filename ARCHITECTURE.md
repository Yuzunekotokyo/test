# PianoProgress アーキテクチャ設計

## 1. アーキテクチャ概要

### アーキテクチャパターン
本アプリケーションは **MVVM (Model-View-ViewModel)** パターンをベースに、**Repository パターン**を組み合わせた構成を採用します。

```
┌─────────────────────────────────────┐
│           View (SwiftUI)            │
│  - ContentView                      │
│  - HomeView, PracticeView, etc.     │
└─────────────┬───────────────────────┘
              │ Binding/@Published
              ▼
┌─────────────────────────────────────┐
│         ViewModel                   │
│  - HomeViewModel                    │
│  - PracticeSessionViewModel         │
│  - ObservableObject                 │
└─────────────┬───────────────────────┘
              │ Business Logic
              ▼
┌─────────────────────────────────────┐
│         Repository                  │
│  - PracticeSessionRepository        │
│  - PieceRepository                  │
└─────────────┬───────────────────────┘
              │ Data Access
              ▼
┌─────────────────────────────────────┐
│      Data Layer (SwiftData)         │
│  - PracticeSession                  │
│  - Piece, PracticeGoal              │
└─────────────────────────────────────┘
```

## 2. ディレクトリ構造

```
PianoProgress/
├── App/
│   ├── PianoProgressApp.swift          # アプリエントリーポイント
│   └── AppConfiguration.swift          # アプリ設定
│
├── Models/
│   ├── PracticeSession.swift           # 練習セッションモデル
│   ├── Piece.swift                     # 練習曲モデル
│   ├── PracticeGoal.swift              # 目標モデル
│   └── Enums/
│       ├── Difficulty.swift
│       ├── PieceStatus.swift
│       └── TimeSignature.swift
│
├── ViewModels/
│   ├── HomeViewModel.swift
│   ├── PracticeSessionViewModel.swift
│   ├── PieceListViewModel.swift
│   ├── StatisticsViewModel.swift
│   └── SettingsViewModel.swift
│
├── Views/
│   ├── Main/
│   │   └── MainTabView.swift           # メインタブビュー
│   ├── Home/
│   │   ├── HomeView.swift
│   │   ├── TodayProgressCard.swift
│   │   └── QuickStartButton.swift
│   ├── Practice/
│   │   ├── PracticeView.swift
│   │   ├── MetronomeView.swift
│   │   ├── TimerView.swift
│   │   └── SessionEndView.swift
│   ├── History/
│   │   ├── HistoryView.swift
│   │   ├── CalendarView.swift
│   │   └── StatisticsChartsView.swift
│   ├── Pieces/
│   │   ├── PieceListView.swift
│   │   ├── PieceDetailView.swift
│   │   ├── PieceEditView.swift
│   │   └── Components/
│   │       └── PieceCard.swift
│   └── Settings/
│       ├── SettingsView.swift
│       ├── GoalSettingsView.swift
│       └── NotificationSettingsView.swift
│
├── Repositories/
│   ├── PracticeSessionRepository.swift
│   ├── PieceRepository.swift
│   └── PracticeGoalRepository.swift
│
├── Services/
│   ├── MetronomeService.swift          # メトロノーム機能
│   ├── NotificationService.swift       # 通知サービス
│   ├── StatisticsService.swift         # 統計計算
│   └── AudioService.swift              # 音声再生
│
├── Utilities/
│   ├── Extensions/
│   │   ├── Date+Extensions.swift
│   │   ├── TimeInterval+Extensions.swift
│   │   └── Color+Extensions.swift
│   ├── Constants.swift
│   └── Helpers.swift
│
└── Resources/
    ├── Assets.xcassets/
    ├── Sounds/
    │   ├── metronome_click.wav
    │   └── metronome_accent.wav
    └── Localizable.strings
```

## 3. レイヤー別詳細設計

### 3.1 Model Layer

#### SwiftDataモデル
SwiftDataの`@Model`マクロを使用してデータの永続化を行います。

```swift
import SwiftData
import Foundation

@Model
final class PracticeSession {
    @Attribute(.unique) var id: UUID
    var startTime: Date
    var endTime: Date?
    var notes: String
    var tempo: Int?
    var createdAt: Date

    @Relationship(deleteRule: .nullify) var pieces: [Piece]

    var duration: TimeInterval {
        guard let endTime = endTime else {
            return Date().timeIntervalSince(startTime)
        }
        return endTime.timeIntervalSince(startTime)
    }

    init(startTime: Date = Date()) {
        self.id = UUID()
        self.startTime = startTime
        self.notes = ""
        self.createdAt = Date()
        self.pieces = []
    }
}
```

### 3.2 Repository Layer

Repositoryパターンでデータアクセスを抽象化し、ViewModelからデータソースの詳細を隠蔽します。

```swift
import SwiftData
import Foundation

@MainActor
protocol PracticeSessionRepositoryProtocol {
    func fetchAll() -> [PracticeSession]
    func fetch(by id: UUID) -> PracticeSession?
    func fetchSessions(from startDate: Date, to endDate: Date) -> [PracticeSession]
    func save(_ session: PracticeSession) throws
    func delete(_ session: PracticeSession) throws
}

@MainActor
final class PracticeSessionRepository: PracticeSessionRepositoryProtocol {
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

    func fetch(by id: UUID) -> PracticeSession? {
        let predicate = #Predicate<PracticeSession> { $0.id == id }
        let descriptor = FetchDescriptor(predicate: predicate)
        return try? modelContext.fetch(descriptor).first
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
```

### 3.3 ViewModel Layer

ViewModelはビジネスロジックを担当し、`ObservableObject`プロトコルに準拠します。

```swift
import Foundation
import Observation

@Observable
@MainActor
final class PracticeSessionViewModel {
    // MARK: - Properties
    private let repository: PracticeSessionRepositoryProtocol
    private(set) var currentSession: PracticeSession?
    private(set) var isSessionActive: Bool = false

    var selectedPieces: [Piece] = []
    var sessionNotes: String = ""

    // MARK: - Initialization
    init(repository: PracticeSessionRepositoryProtocol) {
        self.repository = repository
    }

    // MARK: - Public Methods
    func startSession() {
        let session = PracticeSession()
        session.pieces = selectedPieces
        currentSession = session
        isSessionActive = true
    }

    func endSession() {
        guard let session = currentSession else { return }

        session.endTime = Date()
        session.notes = sessionNotes

        do {
            try repository.save(session)
            resetSession()
        } catch {
            // Handle error
            print("Failed to save session: \(error)")
        }
    }

    func pauseSession() {
        // Implement pause logic if needed
    }

    private func resetSession() {
        currentSession = nil
        isSessionActive = false
        selectedPieces = []
        sessionNotes = ""
    }
}
```

### 3.4 View Layer

SwiftUIを使用した宣言的なUI構築。

```swift
import SwiftUI

struct PracticeView: View {
    @State private var viewModel: PracticeSessionViewModel
    @State private var showMetronome = false

    var body: some View {
        VStack(spacing: 20) {
            if viewModel.isSessionActive {
                ActiveSessionView(viewModel: viewModel)
            } else {
                IdleSessionView(viewModel: viewModel)
            }

            if showMetronome {
                MetronomeView()
            }
        }
        .navigationTitle("練習")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    showMetronome.toggle()
                } label: {
                    Image(systemName: "metronome")
                }
            }
        }
    }
}
```

## 4. サービス層の設計

### 4.1 MetronomeService

AVFoundationを使用したメトロノーム機能。

```swift
import AVFoundation
import Observation

@Observable
@MainActor
final class MetronomeService {
    // MARK: - Properties
    private var audioEngine: AVAudioEngine?
    private var playerNode: AVAudioPlayerNode?
    private var timer: Timer?

    private(set) var isPlaying: Bool = false
    var bpm: Int = 120 {
        didSet { updateTimer() }
    }
    var timeSignature: TimeSignature = .fourFour

    // MARK: - Public Methods
    func start() {
        setupAudioEngine()
        startTimer()
        isPlaying = true
    }

    func stop() {
        timer?.invalidate()
        timer = nil
        audioEngine?.stop()
        isPlaying = false
    }

    func toggle() {
        if isPlaying {
            stop()
        } else {
            start()
        }
    }

    // MARK: - Private Methods
    private func setupAudioEngine() {
        audioEngine = AVAudioEngine()
        playerNode = AVAudioPlayerNode()

        guard let engine = audioEngine, let player = playerNode else { return }

        engine.attach(player)
        engine.connect(player, to: engine.mainMixerNode, format: nil)

        do {
            try engine.start()
        } catch {
            print("Audio engine failed to start: \(error)")
        }
    }

    private func startTimer() {
        let interval = 60.0 / Double(bpm)
        timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
            self?.playClick()
        }
    }

    private func updateTimer() {
        if isPlaying {
            stop()
            start()
        }
    }

    private func playClick() {
        // Play metronome sound
        // Implementation details...
    }
}
```

### 4.2 StatisticsService

統計データの計算を担当するサービス。

```swift
import Foundation

struct StatisticsService {
    // MARK: - Daily Statistics
    static func totalPracticeTime(for sessions: [PracticeSession]) -> TimeInterval {
        sessions.reduce(0) { $0 + $1.duration }
    }

    static func practiceTimeForToday(sessions: [PracticeSession]) -> TimeInterval {
        let today = Calendar.current.startOfDay(for: Date())
        let tomorrow = Calendar.current.date(byAdding: .day, value: 1, to: today)!

        let todaySessions = sessions.filter { session in
            session.startTime >= today && session.startTime < tomorrow
        }

        return totalPracticeTime(for: todaySessions)
    }

    // MARK: - Weekly Statistics
    static func practiceTimeForWeek(sessions: [PracticeSession]) -> TimeInterval {
        let calendar = Calendar.current
        let now = Date()
        let weekStart = calendar.dateInterval(of: .weekOfYear, for: now)?.start ?? now

        let weekSessions = sessions.filter { $0.startTime >= weekStart }
        return totalPracticeTime(for: weekSessions)
    }

    // MARK: - Streak Calculation
    static func calculateStreak(sessions: [PracticeSession]) -> Int {
        let calendar = Calendar.current
        var streak = 0
        var currentDate = calendar.startOfDay(for: Date())

        let sessionsByDate = Dictionary(grouping: sessions) { session in
            calendar.startOfDay(for: session.startTime)
        }

        while sessionsByDate[currentDate] != nil {
            streak += 1
            currentDate = calendar.date(byAdding: .day, value: -1, to: currentDate)!
        }

        return streak
    }

    // MARK: - Piece Statistics
    static func practiceTimeByPiece(sessions: [PracticeSession]) -> [UUID: TimeInterval] {
        var pieceTimeMap: [UUID: TimeInterval] = [:]

        for session in sessions {
            let timePerPiece = session.duration / Double(max(session.pieces.count, 1))
            for piece in session.pieces {
                pieceTimeMap[piece.id, default: 0] += timePerPiece
            }
        }

        return pieceTimeMap
    }
}
```

## 5. 依存性注入

アプリ全体でDependency Injectionを使用して、テスタビリティと保守性を向上させます。

```swift
import SwiftUI
import SwiftData

@main
struct PianoProgressApp: App {
    let modelContainer: ModelContainer

    init() {
        do {
            modelContainer = try ModelContainer(
                for: PracticeSession.self, Piece.self, PracticeGoal.self
            )
        } catch {
            fatalError("Failed to initialize ModelContainer: \(error)")
        }
    }

    var body: some Scene {
        WindowGroup {
            MainTabView()
                .modelContainer(modelContainer)
                .environment(\.repositories, makeRepositories())
        }
    }

    private func makeRepositories() -> Repositories {
        let context = modelContainer.mainContext
        return Repositories(
            practiceSessionRepository: PracticeSessionRepository(modelContext: context),
            pieceRepository: PieceRepository(modelContext: context),
            goalRepository: PracticeGoalRepository(modelContext: context)
        )
    }
}

// Repository Container
struct Repositories {
    let practiceSessionRepository: PracticeSessionRepositoryProtocol
    let pieceRepository: PieceRepositoryProtocol
    let goalRepository: PracticeGoalRepositoryProtocol
}

// Environment Key for DI
private struct RepositoriesKey: EnvironmentKey {
    static let defaultValue = Repositories(
        practiceSessionRepository: PracticeSessionRepository(modelContext: ModelContext()),
        pieceRepository: PieceRepository(modelContext: ModelContext()),
        goalRepository: PracticeGoalRepository(modelContext: ModelContext())
    )
}

extension EnvironmentValues {
    var repositories: Repositories {
        get { self[RepositoriesKey.self] }
        set { self[RepositoriesKey.self] = newValue }
    }
}
```

## 6. エラーハンドリング

統一的なエラーハンドリング戦略。

```swift
enum AppError: LocalizedError {
    case dataFetchFailed
    case dataSaveFailed
    case invalidData
    case audioEngineFailure

    var errorDescription: String? {
        switch self {
        case .dataFetchFailed:
            return "データの取得に失敗しました"
        case .dataSaveFailed:
            return "データの保存に失敗しました"
        case .invalidData:
            return "無効なデータです"
        case .audioEngineFailure:
            return "オーディオエンジンの起動に失敗しました"
        }
    }
}
```

## 7. テスト戦略

### 7.1 ユニットテスト
- ViewModelのビジネスロジックテスト
- Repositoryのデータアクセステスト
- Serviceの機能テスト

### 7.2 UIテスト
- 主要なユーザーフローのE2Eテスト
- アクセシビリティテスト

### 7.3 モック・スタブの活用
Repositoryのプロトコル準拠により、テスト時はモックRepositoryを使用。

```swift
final class MockPracticeSessionRepository: PracticeSessionRepositoryProtocol {
    var sessions: [PracticeSession] = []

    func fetchAll() -> [PracticeSession] {
        return sessions
    }

    func save(_ session: PracticeSession) throws {
        sessions.append(session)
    }

    // Other methods...
}
```

## 8. パフォーマンス最適化

### データフェッチ
- SwiftDataの`FetchDescriptor`で必要なデータのみ取得
- ページネーション実装（履歴一覧など）

### UI描画
- `LazyVStack`, `LazyHStack`の活用
- 重い処理は`Task`で非同期実行

### メモリ管理
- 画像などのリソースは適切に解放
- 長時間セッションでのメモリリーク防止

## 9. セキュリティ・プライバシー

- すべてのデータはローカルストレージに保存
- 外部へのデータ送信なし
- アプリのプライバシーポリシーを明示

---

**最終更新**: 2026年1月20日
