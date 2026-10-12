# popdex-mmbot

PopDEX 向けのマーケットメイク bot。リベート（メーカー手数料のマイナス分）を主な収益源にしつつ、
注文の間隔・サイズ・Taker 混在を乱数化して「張り付きの高頻度 bot」ではなく
裁量トレーダー程度の活動量に抑える設計です。

```
mmbot/
  engine.py            メインループ（価格取得 → リスク判定 → Taker 判断 → 指値の張り替え）
  strategy/quoting.py  フェアバリュー ± スプレッド、在庫スキュー、Funding 補正
  strategy/humanizer.py ペーシング（ランダム待機・休憩・活動時間帯・1日の取引回数予算・サイズ乱数・Taker 比率）
  risk.py              1日損失上限 / 最大DD / レバレッジ / 価格鮮度 / 注文レート上限
  exchange/base.py     取引所アダプタの抽象クラス
  exchange/paper.py    ペーパー取引所（外部価格に追随して約定をシミュレート）
  exchange/popdex.py   PopDEX アダプタ（**エンドポイント・署名は TODO**）
  feeds/binance.py     Binance の板中値をフェアバリューとして使用（取引はしない）
  journal.py           fills.csv / snapshots.csv に記録
```

## セットアップ

```bash
cd popdex-mmbot
pip install -r requirements.txt
cp config.example.yaml config.yaml   # 編集
python -m pytest -q                  # 戦略・リスクの単体テスト
python run.py --offline              # ネット無しのランダムウォークでペーパー
python run.py                        # Binance 価格でペーパー（dry_run: true）
```

## PopDEX に接続する手順

PopDEX の発注は REST ではなく **自前チェーンのコントラクト呼び出し**（Order precompile）で、
認証は「メインウォレットが承認した Agent Key で tx に署名する」方式です。
詳細は `docs/popdex-api-notes.md`。

```bash
# 1. Agent Key を作ってメインウォレットから承認（メイン秘密鍵はこの 1 回だけ使う）
read -rs MAIN_PRIVATE_KEY && export MAIN_PRIVATE_KEY
python scripts/approve_agent.py --testnet   # まず testnet。本番は --testnet 無し
unset MAIN_PRIVATE_KEY
#   -> agent_key.ini が出来る（gitignore 済み。絶対に共有しない。発注・取消のみ可、出金不可）

# 2. REST の読み取りパス / フィールド名を確認
python scripts/probe.py --config config.yaml

# 3. testnet で最小サイズの発注・取消が通るか確認し、config.yaml の popdex: 以下の
#    VERIFY 項目（enum 値・小数桁・cancelOrder ABI）を確定させる

# 4. 本番
#    exchange.name: popdex / popdex.network: mainnet / dry_run: false
python run.py
```

## 本番前に必ずやること

1. `docs/popdex-api-notes.md` の「要確認」項目を testnet で確定する（enum 値、price/qty の桁、
   `cancelOrder` の ABI、REST パス）。本番口座に対して未確認のまま流さない
2. `market.tick_size` / `lot_size` / `min_notional_usd` を実際の銘柄仕様に合わせる
3. `exchange.maker_fee_bps` / `taker_fee_bps` を自分の VIP ティアの値にする
4. 小さいサイズ（`order_notional_min/max_usd` を 10〜30）で数日回し、`logs/` を確認してから拡大する
5. レート制限: RPC 1,200 重み/分、未約定注文 500 件/口座、nonce はミリ秒で単調増加（アダプタが保証）

## 設計メモ

- **収益の源泉**: リベート + スプレッド。Taker は在庫を平らにする用途が 7 割、残り 3 割は
  「普通に買う／売る」用途で、活動を単調にしないためのもの。Taker の手数料はコストなので
  `taker_ratio` を上げすぎない。
- **在庫スキュー**: ポジションが上限に近づくほど両側の気配をずらし、反対側が約定しやすくする。
  上限に達した側は気配を出さない。
- **止まる条件**: 1日損失 5% / 最大DD 10% / 参照価格が 20 秒以上古い / 板スプレッド異常 /
  Funding が極端。止まる時は必ず全注文キャンセル。
- **資金 800 USD** の既定値: ポジション上限 400 USD（約 0.5 倍）、レバレッジ上限 1.5 倍。
  100 倍まで使えても MM で使う理由はない。
