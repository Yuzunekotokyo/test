# popdex-mmbot — Claude への作業指示

このフォルダは PopDEX（招待制の無期限先物 DEX、独自チェーン chainId 2184）向けの
マーケットメイク bot。Python 3.11+ / asyncio。オーナーは実資金約 800 USD の口座で
裁量取引中。bot はまだ **ペーパー取引のみ動作確認済み**、本番接続は未検証。

## まず読むもの

1. `README.md` — 構成と起動手順
2. `docs/popdex-api-notes.md` — PopDEX の接続仕様（判明分と「要確認」の一覧）
3. `config.example.yaml` — `popdex:` セクションの `VERIFY` 付き項目が未確定値

## 確定している事実（変更しない）

- 発注・取消は REST ではなく Order precompile `0x…1000` への署名 tx。gasPrice 0、
  nonce はミリ秒タイムスタンプで**単調増加必須**（`NonceSource` が担保）。RPC はバッチ不可。
- 認証は Agent Key（メインウォレットが `approveAgent` で承認した別鍵）。発注・取消のみ可、出金不可。
  `agent_key.ini` は **絶対にコミットしない**（.gitignore 済み）。中身をログやチャットに出さない。
- WebSocket のハートビートは文字列 `ping`（JSON ではない）。
- 手数料: **マイナス手数料（リベート）は MM ティア限定**（14 日出来高 ≥ $1.5 億 または
  メーカーシェア ≥ 0.25%、個別審査）。800 USD 口座では到達不能。通常ティアの Maker/Taker 率は未確認。
- `clientOrderId` は英数字とハイフンのみ（`_` `.` は revert）。
- REST の `50002` は汎用パラメータエラー。「非対応シンボル」と解釈しない。

## 未確定（本番前に testnet で必ず確定する）

`config.yaml` の `popdex:` で調整できる:

- orderParams の enum 数値（Limit/Market、Buy/Sell、PostOnly/IOC/GTC）
- `price` / `qty` の固定小数桁（1e18 と仮定）
- `cancelOrder` の ABI（記事に無い。仮置き）
- REST 読み取りパスとフィールド名（`scripts/probe.py` の出力で合わせる）
- 通常 VIP ティアの手数料 → `exchange.maker_fee_bps` / `taker_fee_bps`

**これらが未確定のまま `dry_run: false` + `network: mainnet` で起動しない。**
PostOnly のつもりが成行になる可能性がある。

## 作業ルール

- 変更後は必ず `python -m pytest -q` と `timeout 20 python run.py --offline` を通す。
- 戦略（`strategy/`）・リスク（`risk.py`）・取引所アダプタ（`exchange/`）の境界を崩さない。
  PopDEX のワイヤフォーマットを知っていいのは `exchange/popdex.py` だけ。
- リスク上限（1 日損失 5%、最大 DD 10%、ポジション上限 400 USD、レバ 1.5 倍）を
  オーナーの明示的な指示なしに緩めない。
- 「人間らしさ」(`strategy/humanizer.py`) は注文間隔・サイズ・Taker 比率の乱数化まで。
  ウォッシュトレード、セルフ約定、出来高の水増しに当たる機能は実装しない。
- コミットメッセージにモデル名を書かない。
- 秘密鍵・シード・`agent_key.ini` の内容を読んでも出力しない。

## 次にやるべきこと（優先順）

1. オーナーから手数料ページ全文（通常ティア）をもらい、bot を回す経済合理性を判断する。
   Maker 手数料が正なら、スプレッド取り戦略に設計を組み替えるか、bot 自体を見送る提案をする。
2. testnet で `scripts/approve_agent.py --testnet` → `scripts/probe.py` → 最小サイズの
   発注・取消を通し、`VERIFY` 項目を確定して `config.example.yaml` と `docs/` を更新する。
3. 任意: Telegram 通知と遠隔停止（iPhone からの監視用）。
4. 任意: WebSocket `books1` で板を取り、REST ポーリングを減らす。

## オーナーの希望（会話より）

- リベートを狙いたかったが、上記の通り MM ティア限定と判明。
- 機械的すぎる挙動は避けたい: Taker を混ぜ、数量をランダムに、取引回数は人間レベル
  （既定: 1 日 15〜50 回、Taker 比率 20%、活動時間 8〜24 時 JST）。
- iPhone からの取引: Safari で `https://app.popdex.xyz/ja/trade/futures/BTCUSDT` を
  開きホーム画面に追加する案を提示済み。専用 iOS アプリは無し。
- 説明には簡単なたとえ話を添える。謝罪や言い訳は不要。
