# PianoProgress 実装ロードマップ

## プロジェクト概要

本ドキュメントは、PianoProgressアプリの実装計画を段階的に示したロードマップです。各フェーズは独立して完結し、ユーザーに価値を提供できる機能セットを含んでいます。

## 開発原則

1. **段階的なリリース**: 各フェーズで動作するアプリをリリース可能な状態に保つ
2. **ユーザー中心**: 各フェーズで最も価値の高い機能を優先
3. **技術的負債の最小化**: 拡張性を考慮した設計
4. **テスト駆動**: 各機能に対してテストを作成

---

## Phase 1: MVP (最小機能製品) - 基礎構築

**目標**: ピアノ練習の記録と基本的な統計機能を提供

### 1.1 プロジェクトセットアップ
- [x] Xcodeプロジェクト作成
- [ ] SwiftDataモデルコンテナの設定
- [ ] 基本的なアプリ構造（MVVM）の構築
- [ ] ディレクトリ構造の整理
- [ ] Git管理の設定

**期待成果**: ビルド可能な基礎アプリケーション

### 1.2 データモデルの実装
- [ ] `PracticeSession`モデルの実装
- [ ] `Piece`モデルの実装
- [ ] 列挙型（Difficulty, PieceStatus等）の実装
- [ ] モデル間のリレーションシップ設定

**ファイル**:
- `Models/PracticeSession.swift`
- `Models/Piece.swift`
- `Models/Enums/Difficulty.swift`
- `Models/Enums/PieceStatus.swift`

### 1.3 Repository層の実装
- [ ] `PracticeSessionRepository`の実装
- [ ] `PieceRepository`の実装
- [ ] Repositoryプロトコルの定義
- [ ] 依存性注入の設定

**ファイル**:
- `Repositories/PracticeSessionRepository.swift`
- `Repositories/PieceRepository.swift`

### 1.4 基本ナビゲーション
- [ ] タブビューの実装（5タブ）
- [ ] 各タブの空ビュー作成
- [ ] ナビゲーションの基本構造

**ファイル**:
- `Views/Main/MainTabView.swift`
- `Views/Home/HomeView.swift`
- `Views/Practice/PracticeView.swift`
- `Views/History/HistoryView.swift`
- `Views/Pieces/PieceListView.swift`
- `Views/Settings/SettingsView.swift`

### 1.5 練習セッション機能
- [ ] セッション開始・終了のUI
- [ ] タイマー表示
- [ ] セッション記録機能
- [ ] `PracticeSessionViewModel`の実装

**ファイル**:
- `ViewModels/PracticeSessionViewModel.swift`
- `Views/Practice/PracticeView.swift`
- `Views/Practice/TimerView.swift`
- `Views/Practice/SessionEndView.swift`

### 1.6 曲リスト管理
- [ ] 曲の一覧表示
- [ ] 曲の追加フォーム
- [ ] 曲の編集・削除機能
- [ ] `PieceListViewModel`の実装

**ファイル**:
- `ViewModels/PieceListViewModel.swift`
- `Views/Pieces/PieceListView.swift`
- `Views/Pieces/PieceEditView.swift`
- `Views/Pieces/Components/PieceCard.swift`

### 1.7 基本統計機能
- [ ] 今日の練習時間表示
- [ ] 総練習時間表示
- [ ] 簡易的な履歴一覧
- [ ] `StatisticsService`の基本実装

**ファイル**:
- `Services/StatisticsService.swift`
- `ViewModels/HomeViewModel.swift`
- `Views/Home/TodayProgressCard.swift`

### 1.8 簡易メトロノーム
- [ ] 基本的なメトロノーム機能（BPM調整のみ）
- [ ] 再生・停止機能
- [ ] `MetronomeService`の基本実装

**ファイル**:
- `Services/MetronomeService.swift`
- `Services/AudioService.swift`
- `Views/Practice/MetronomeView.swift`

### Phase 1 完了条件
- ✅ 練習セッションを開始・終了できる
- ✅ 曲を追加・管理できる
- ✅ 今日の練習時間が表示される
- ✅ 基本的なメトロノームが使える
- ✅ すべての画面がナビゲート可能

---

## Phase 2: コア機能の充実

**目標**: より詳細な練習管理と統計機能を提供

### 2.1 メトロノーム機能の拡張
- [ ] 拍子設定（2/4, 3/4, 4/4等）
- [ ] アクセント設定
- [ ] 視覚的なビートインジケーター
- [ ] バックグラウンド再生対応

**ファイル**:
- `Models/Enums/TimeSignature.swift`
- `Services/MetronomeService.swift` (拡張)
- `Views/Practice/MetronomeView.swift` (拡張)

### 2.2 練習履歴のカレンダービュー
- [ ] 月次カレンダーの実装
- [ ] 練習した日のマーク表示
- [ ] 日付選択で詳細表示
- [ ] カスタムカレンダーコンポーネント

**ファイル**:
- `Views/History/CalendarView.swift`
- `Views/History/DayDetailView.swift`
- `ViewModels/HistoryViewModel.swift`

### 2.3 詳細統計とグラフ
- [ ] 週間練習時間の棒グラフ
- [ ] 月間練習時間の折れ線グラフ
- [ ] 曲別練習時間の円グラフ
- [ ] Swift Chartsの統合

**ファイル**:
- `Views/History/StatisticsChartsView.swift`
- `ViewModels/StatisticsViewModel.swift`
- `Services/StatisticsService.swift` (拡張)

### 2.4 練習目標機能
- [ ] `PracticeGoal`モデルの実装
- [ ] 目標設定UI
- [ ] 目標進捗の可視化
- [ ] 達成状況の表示

**ファイル**:
- `Models/PracticeGoal.swift`
- `Repositories/PracticeGoalRepository.swift`
- `Views/Settings/GoalSettingsView.swift`
- `Views/Home/GoalProgressView.swift`

### 2.5 検索・フィルタ機能
- [ ] 曲の検索機能
- [ ] ステータスでのフィルタ
- [ ] 難易度でのフィルタ
- [ ] タグでのフィルタ

**ファイル**:
- `Views/Pieces/SearchBar.swift`
- `Views/Pieces/FilterView.swift`
- `ViewModels/PieceListViewModel.swift` (拡張)

### 2.6 練習ストリーク機能
- [ ] 連続練習日数の計算
- [ ] ホーム画面でのストリーク表示
- [ ] ストリーク継続のモチベーション表示

**ファイル**:
- `Services/StatisticsService.swift` (ストリーク計算)
- `Views/Home/StreakCard.swift`

### 2.7 セッションと曲の関連付け強化
- [ ] セッション開始時に曲を選択
- [ ] 複数曲の同時練習対応
- [ ] 曲ごとの練習時間配分

**ファイル**:
- `Views/Practice/PieceSelectionView.swift`
- `ViewModels/PracticeSessionViewModel.swift` (拡張)

### Phase 2 完了条件
- ✅ カレンダーで練習履歴を確認できる
- ✅ 詳細な統計グラフが表示される
- ✅ 練習目標を設定し、進捗を追跡できる
- ✅ メトロノームで拍子・アクセントを設定できる
- ✅ 曲の検索・フィルタができる

---

## Phase 3: ユーザー体験の向上

**目標**: アプリの使いやすさと魅力を高める

### 3.1 通知機能
- [ ] `NotificationService`の実装
- [ ] 通知パーミッション取得
- [ ] 練習リマインダーの設定UI
- [ ] カスタム通知スケジュール

**ファイル**:
- `Services/NotificationService.swift`
- `Views/Settings/NotificationSettingsView.swift`

### 3.2 メモ機能の充実
- [ ] リッチテキストメモ
- [ ] セッションメモの一覧・編集
- [ ] 曲ごとのメモ管理
- [ ] メモ検索機能

**ファイル**:
- `Views/Components/RichTextEditor.swift`
- `Views/Pieces/PieceNotesView.swift`
- `Views/History/SessionNotesView.swift`

### 3.3 音楽理論リファレンス
- [ ] スケール一覧の実装
- [ ] コード一覧の実装
- [ ] サークル・オブ・フィフス
- [ ] インタラクティブな参照UI

**ファイル**:
- `Views/Settings/MusicTheory/ScalesView.swift`
- `Views/Settings/MusicTheory/ChordsView.swift`
- `Views/Settings/MusicTheory/CircleOfFifthsView.swift`

### 3.4 アニメーション・トランジション
- [ ] スムーズな画面遷移
- [ ] マイクロインタラクション
- [ ] 統計グラフのアニメーション
- [ ] タイマーのビジュアルエフェクト

**ファイル**:
- `Utilities/Animations.swift`
- 各Viewファイルでのアニメーション追加

### 3.5 ダークモード最適化
- [ ] カラースキームの最適化
- [ ] ダークモード専用アセット
- [ ] コントラストの調整

**ファイル**:
- `Utilities/Extensions/Color+Extensions.swift`
- `Resources/Assets.xcassets/` (カラーセット)

### 3.6 アクセシビリティ対応
- [ ] VoiceOver対応
- [ ] Dynamic Type対応
- [ ] アクセシビリティラベルの追加
- [ ] 色覚異常への配慮

**ファイル**:
- すべてのViewファイルでアクセシビリティ対応

### 3.7 オンボーディング
- [ ] 初回起動時のチュートリアル
- [ ] 機能説明スライド
- [ ] サンプルデータの作成オプション

**ファイル**:
- `Views/Onboarding/OnboardingView.swift`
- `Views/Onboarding/WelcomeView.swift`

### Phase 3 完了条件
- ✅ 練習リマインダーが設定できる
- ✅ メモ機能が充実している
- ✅ 音楽理論リファレンスが参照できる
- ✅ アニメーションがスムーズ
- ✅ VoiceOverで操作可能

---

## Phase 4: 拡張機能

**目標**: より高度な機能でアプリの価値を最大化

### 4.1 データエクスポート
- [ ] CSV形式でのエクスポート
- [ ] PDF形式でのレポート生成
- [ ] 月次レポートの自動生成
- [ ] シェア機能

**ファイル**:
- `Services/ExportService.swift`
- `Views/Settings/ExportView.swift`

### 4.2 iCloud同期
- [ ] CloudKitの統合
- [ ] データの自動同期
- [ ] 競合解決ロジック
- [ ] 同期状態の表示

**ファイル**:
- `Services/CloudSyncService.swift`
- SwiftDataのCloudKit設定

### 4.3 ウィジェット
- [ ] 今日の練習時間ウィジェット
- [ ] 練習ストリークウィジェット
- [ ] クイックスタートウィジェット
- [ ] WidgetKitの統合

**ファイル**:
- `Widgets/TodayPracticeWidget.swift`
- `Widgets/StreakWidget.swift`

### 4.4 Apple Watch対応
- [ ] Watch用コンパニオンアプリ
- [ ] タイマー機能
- [ ] シンプルなメトロノーム
- [ ] 今日の練習時間表示

**ファイル**:
- `WatchApp/` (新規ターゲット)

### 4.5 録音機能（オプション）
- [ ] 練習の録音機能
- [ ] 録音の再生・管理
- [ ] セッションへの録音紐付け

**ファイル**:
- `Services/RecordingService.swift`
- `Views/Practice/RecordingView.swift`

### 4.6 高度な統計
- [ ] 時間帯別の練習パターン分析
- [ ] 曲の習得速度分析
- [ ] 週間・月間比較
- [ ] トレンド予測

**ファイル**:
- `Services/AdvancedAnalyticsService.swift`
- `Views/History/AdvancedStatisticsView.swift`

### 4.7 ソーシャル機能（検討中）
- [ ] 練習記録のシェア
- [ ] 目標達成のシェア
- [ ] オプトインベースの比較機能

### Phase 4 完了条件
- ✅ データをエクスポートできる
- ✅ iCloudで同期できる
- ✅ ホーム画面ウィジェットが使える
- ✅ Apple Watchで練習を記録できる

---

## 技術的考慮事項

### パフォーマンス
- SwiftDataのインデックス最適化
- 画像・音声リソースの遅延読み込み
- メモリリーク対策
- バックグラウンドタスクの効率化

### テスト
- 各フェーズでユニットテストを作成
- UIテストの重要フローへの適用
- テストカバレッジ目標: 70%以上

### CI/CD
- GitHub Actionsでの自動ビルド
- TestFlightへの自動デプロイ
- ベータテスター管理

### セキュリティ
- 個人情報の適切な管理
- データの暗号化（必要に応じて）
- プライバシーポリシーの整備

---

## マイルストーン

| フェーズ | 主要機能 | 状態 |
|---------|---------|------|
| Phase 1 | MVP - 基本的な練習記録 | 🔵 計画中 |
| Phase 2 | 詳細統計・目標管理 | ⚪ 未着手 |
| Phase 3 | UX向上・通知・リファレンス | ⚪ 未着手 |
| Phase 4 | iCloud・ウィジェット・Watch | ⚪ 未着手 |

---

## 次のステップ

1. **Phase 1のタスクを開始**
   - プロジェクトセットアップ
   - データモデルの実装から着手

2. **デザインモックアップの作成**
   - Figmaでの画面設計
   - ユーザーフローの確認

3. **開発環境の整備**
   - Xcodeプロジェクトの設定
   - 依存関係の管理

---

**最終更新**: 2026年1月20日
**次回レビュー予定**: Phase 1完了後
