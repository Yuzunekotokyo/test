# ピアノ練習支援アプリ 設計ドキュメント

## 1. アプリ概要

### アプリ名（仮）
**PianoProgress** - ピアノ演奏の練習を効率的に管理・追跡するiOSアプリ

### コンセプト
ピアノ学習者が日々の練習を記録し、進捗を可視化し、効率的な練習をサポートするアプリケーション

### ターゲットユーザー
- 初級〜中級のピアノ学習者
- 独学でピアノを学ぶ人
- 練習の習慣化を目指す人
- 自分の成長を記録したい人

## 2. 主要機能

### 2.1 コア機能

#### メトロノーム機能
- BPM調整（30-300 BPM）
- 拍子設定（2/4, 3/4, 4/4, 5/4, 6/8等）
- アクセント設定
- 視覚的なビート表示
- バックグラウンド再生対応

#### 練習セッション管理
- 練習開始・終了のタイマー
- 練習内容の記録（曲名、練習項目）
- セッションごとのメモ機能
- 練習時間の自動記録

#### 練習曲リスト管理
- 曲の登録・編集・削除
- 曲ごとの難易度設定
- 曲のステータス管理（練習中、マスター済み等）
- 作曲者・ジャンルのタグ付け

### 2.2 進捗管理機能

#### 練習履歴
- カレンダービューでの練習日の可視化
- 日別・週別・月別の練習時間統計
- 曲ごとの累計練習時間
- 練習ストリーク（連続練習日数）

#### 目標設定
- 日別練習時間の目標設定
- 週間・月間の目標設定
- 目標達成の通知
- 進捗率の表示

#### 統計・分析
- 練習時間のグラフ表示
- 曲別練習時間の円グラフ
- 時間帯別の練習パターン分析
- 週間・月間レポート

### 2.3 サポート機能

#### 練習メモ
- セッションごとのメモ
- 曲ごとの永続的なメモ
- 難所のマーキング
- テクニックのヒント記録

#### 音楽理論参照
- 基本スケール一覧（長音階、短音階）
- 主要コード一覧
- サークル・オブ・フィフス
- フィンガリング参考図

#### リマインダー
- 練習時間のリマインダー通知
- カスタム通知設定

## 3. 技術スタック

### フレームワーク・言語
- **言語**: Swift 5.9+
- **UIフレームワーク**: SwiftUI
- **最小対応OS**: iOS 17.0+

### データ永続化
- **SwiftData**: メインのデータ永続化層
- **UserDefaults**: 設定情報の保存

### アーキテクチャ
- **MVVM (Model-View-ViewModel)** パターン
- **Repository パターン**: データアクセス層の抽象化

### 主要ライブラリ（標準フレームワーク）
- **AVFoundation**: メトロノーム音源
- **Charts**: グラフ表示（iOS 16+標準）
- **UserNotifications**: 通知機能

## 4. データモデル設計

### 4.1 Practice Session（練習セッション）
```swift
@Model
class PracticeSession {
    var id: UUID
    var startTime: Date
    var endTime: Date?
    var duration: TimeInterval // 秒単位
    var pieces: [Piece] // 練習した曲
    var notes: String // メモ
    var tempo: Int? // 使用したテンポ
    var createdAt: Date
}
```

### 4.2 Piece（練習曲）
```swift
@Model
class Piece {
    var id: UUID
    var title: String
    var composer: String?
    var difficulty: Difficulty
    var status: PieceStatus
    var tags: [String] // ジャンル等
    var notes: String // 曲に関するメモ
    var totalPracticeTime: TimeInterval
    var createdAt: Date
    var lastPracticedAt: Date?
}

enum Difficulty: String, Codable {
    case beginner = "初級"
    case intermediate = "中級"
    case advanced = "上級"
}

enum PieceStatus: String, Codable {
    case learning = "練習中"
    case reviewing = "復習中"
    case mastered = "マスター済み"
    case paused = "保留中"
}
```

### 4.3 Practice Goal（練習目標）
```swift
@Model
class PracticeGoal {
    var id: UUID
    var targetMinutesPerDay: Int
    var targetDaysPerWeek: Int
    var startDate: Date
    var endDate: Date?
    var isActive: Bool
}
```

### 4.4 Settings（設定）
```swift
struct AppSettings {
    var defaultMetronomeBPM: Int = 120
    var defaultTimeSignature: TimeSignature = .fourFour
    var enableNotifications: Bool = true
    var notificationTime: Date?
    var theme: AppTheme = .system
}

enum TimeSignature: String {
    case twoFour = "2/4"
    case threeFour = "3/4"
    case fourFour = "4/4"
    case fiveFour = "5/4"
    case sixEight = "6/8"
}

enum AppTheme: String {
    case light = "ライト"
    case dark = "ダーク"
    case system = "システム"
}
```

## 5. 画面設計

### 5.1 画面構成

#### タブバー構成
1. **ホーム** - 今日の練習状況、クイックアクション
2. **練習開始** - セッション開始、メトロノーム
3. **履歴** - 練習履歴、統計
4. **曲リスト** - 練習曲の管理
5. **設定** - アプリ設定

### 5.2 主要画面詳細

#### ホーム画面
- 今日の練習時間（進捗リング）
- 週間目標の達成状況
- 練習ストリーク表示
- クイックスタートボタン
- 最近練習した曲

#### 練習開始画面
- タイマー（開始/停止/リセット）
- メトロノームコントロール
  - BPMスライダー
  - 拍子選択
  - 再生/停止ボタン
- 練習中の曲選択
- セッション終了時のメモ入力

#### 履歴画面
- カレンダービュー（月表示）
- 練習した日にマーク表示
- 選択した日の練習詳細
- 統計グラフ
  - 週間練習時間の棒グラフ
  - 月間練習時間の推移
  - 曲別練習時間の円グラフ

#### 曲リスト画面
- 検索・フィルタ機能
- ステータス別表示
- 曲カード表示
  - 曲名、作曲者
  - 難易度バッジ
  - 累計練習時間
  - 最終練習日
- スワイプアクション（編集/削除）
- 追加ボタン

#### 曲詳細画面
- 曲の基本情報表示・編集
- 練習履歴タイムライン
- メモセクション
- 統計情報

#### 設定画面
- メトロノーム設定
- 目標設定
- 通知設定
- 音楽理論参照
- データエクスポート
- アプリ情報

## 6. UI/UXデザイン方針

### カラースキーム
- **プライマリカラー**: 深い紫（#5B21B6）- 音楽・芸術的な印象
- **アクセントカラー**: 暖かいゴールド（#F59E0B）- 達成感・モチベーション
- **背景**: システム背景色（ライト/ダーク対応）

### デザイン原則
- **シンプル**: 機能を詰め込みすぎず、使いやすさを優先
- **視覚的フィードバック**: アクションに対する明確なフィードバック
- **一貫性**: iOS Human Interface Guidelinesに準拠
- **アクセシビリティ**: Dynamic Type、VoiceOver対応

## 7. 実装フェーズ

### Phase 1: MVP（最小限の機能）
- [ ] データモデルの実装（SwiftData）
- [ ] 基本的なナビゲーション構造
- [ ] 練習セッションの開始・終了・記録
- [ ] 簡易的なメトロノーム機能
- [ ] 曲リストの追加・表示
- [ ] 基本的な統計表示（合計練習時間）

### Phase 2: コア機能の充実
- [ ] メトロノーム機能の拡張（拍子、アクセント）
- [ ] カレンダービューでの履歴表示
- [ ] 詳細な統計グラフ
- [ ] 練習目標の設定・追跡
- [ ] 検索・フィルタ機能

### Phase 3: ユーザー体験の向上
- [ ] 通知機能の実装
- [ ] メモ・タグ機能の充実
- [ ] 音楽理論リファレンス
- [ ] アニメーション・トランジションの改善
- [ ] ダークモード対応の最適化

### Phase 4: 拡張機能
- [ ] データエクスポート機能（CSV, PDF）
- [ ] iCloud同期
- [ ] ウィジェット対応
- [ ] Apple Watch連携
- [ ] 録音機能（オプション）

## 8. 非機能要件

### パフォーマンス
- アプリ起動時間: 2秒以内
- 画面遷移: スムーズで即座に反応
- データ読み込み: 遅延を感じさせない

### データ
- ローカルストレージ中心
- データの定期的なバックアップ促進
- データ削除時の確認ダイアログ

### セキュリティ
- ユーザーデータはデバイス内に保存
- 外部送信なし（プライバシー重視）

### アクセシビリティ
- VoiceOver完全対応
- Dynamic Type対応
- 色覚異常への配慮（色のみに依存しない）

## 9. 今後の検討事項

- SNSシェア機能の追加
- 他のユーザーとの練習記録比較（オプトイン）
- AIによる練習アドバイス
- 楽譜表示機能
- メトロノーム以外の練習ツール（チューナー等）

---

**最終更新**: 2026年1月20日
**バージョン**: 1.0
