# PopDEX API メモ（yuckey 氏 note 記事 2026-09-21 より）

元記事: https://note.com/like_hyssop8403/n/n02ac7e5b14c4 — ethers v6 (Node) での接続記録。
数値・挙動は記事執筆時点の実測。**仕様は変わりうる。**

## 前提: 注文は REST ではなくコントラクト呼び出し

| 用途 | エンドポイント |
|---|---|
| 発注・取消 | Order precompile `0x0000000000000000000000000000000000001000` |
| 口座・エージェント管理 | Account precompile `0x0000000000000000000000000000000000001008` |
| RPC (mainnet, chainId 2184) | `https://app.popdex.xyz/api/v1/web3/rpc` |
| RPC (testnet, chainId 34952) | `https://testnet-app.popdex.xyz/api/v1/web3/rpc` |
| REST (読み取り) | `https://api.popdex.xyz` |
| WebSocket | `wss://ws.popdex.xyz/v1/ws/public` |

- ガス代なし。ただし tx には `gasPrice: 0` を明示。
- **nonce はミリ秒タイムスタンプ**（連番ではない）。同一ミリ秒に 2 件送ると `-32000 Invalid nonce`。自分で単調増加を保証する。
- RPC は **バッチリクエスト不可**（ethers では `batchMaxCount: 1`。web3.py は既定でバッチしないので問題なし）。

## Agent Key（API キー相当）

- 「API キー発行」ボタンは無い。自分でランダムな鍵を作り、メインウォレットから `approveAgent` で承認する。
- Agent Key は**発注・取消のみ可能、出金不可**。1 口座あたり最大 10 本。
- 入金して口座が作られてから承認すること（未入金だと approveAgent で失敗）。
- 承認の確認: `GET https://api.popdex.xyz/api/v1/account/0x<main>/agents`
- 再作成時は必ず新しい Agent アドレスを使う（リプレイ対策）。testnet と本番で鍵を分ける。

Account precompile ABI（記事より。末尾の引数名は画像で切れている）:

```
function approveAgent(address agent, address delegator, bytes32 name, uint64 expiresAt, uint64 <nonce?>)
function getAgents(address delegator) view returns (address[] agents, uint64[] ...)
```

記事のスクリプトは `approveAgent(agent, main, ZeroHash, 0 /*無期限*/, Date.now())` で呼んでいる。

## 発注: `placeOrder`

```
placeOrder(
  address  main,          // メイン口座
  bytes32  clientOrderId, // 英数字とハイフンのみ。'_' や '.' は revert
  uint16   symbolId,
  bytes32  orderParams,   // 下記
  uint256  price,
  uint256  qty,
  uint256  slippage,      // 18 桁固定小数。0 で無制限
  address  builder,       // 使わなければ ZeroAddress
  uint256  builderFee     // 使わなければ 0
)
```

`orderParams` は 32 バイト、MSB 側から:

| byte | 意味 |
|---|---|
| 0 | category: 2 = Futures |
| 1 | orderType: Limit / Market |
| 2 | side: Buy / Sell |
| 3 | timeInForce: PostOnly / IOC など |
| 4 | marketUnit |
| 5 | BBO 指定 |
| 6 | reduceOnly |
| 7 | positionSide (0 = Oneway) |
| 9 | Self-Trade Prevention |
| 10–15 | 予約。0 |
| 16– | トリガー注文用 |

### 記事に書かれていない＝要確認（`config.yaml` の `popdex:` で調整）

- 各 enum の数値（Limit=?, Market=?, Buy=?, Sell=?, PostOnly=?, IOC=?）
- `price` / `qty` のスケール（slippage が 1e18 なので 1e18 の可能性が高いが未確認）
- `cancelOrder` の ABI
- symbolId ↔ シンボル名の対応（REST の tickers/instruments で取るのが筋）
- REST 読み取りの正確なパス（記事に出てくるのは `/public/market/fills`、`/api/v1/account/<addr>/agents` のみ）

## WebSocket

```json
{"op":"subscribe","args":[
  {"category":"Futures","topic":"books1","symbol":"WIFUSDT"},
  {"walletId":"0x<main>","topic":"order"},
  {"walletId":"0x<main>","topic":"fill"},
  {"walletId":"0x<main>","topic":"position"}
]}
```

- ハートビートは **文字列 `ping`**（JSON ではない）。応答も文字列 `pong`。30 秒間隔で十分。
- order / fill / position は walletId 単位。全シンボル分が同じ接続に流れてくる。

WS 制限（IP 単位、REST と別枠）: 同時接続 10、新規接続 30/分、購読 1,000、送信 2,000/分。

## レート制限

| ヘッダ | 意味 |
|---|---|
| `x-ratelimit-weight-used` | 窓内の累積重み。RPC は 1 呼び出し +1。上限 1,200/分 |
| `x-ratelimit-writequota` / `cancelquota` | 発注 tx の応答にだけ付く。基礎 10,000 に生涯取引高 1 USD あたり +1 |

- quota と重みは **ウォレット/IP 単位**（bot 単位ではない）。
- 同時に持てる未約定注文は **500 件/口座**。
- REST の `50002` は「パラメータ検証失敗」の汎用エラー。板が空のときやパラメータ不足でも出る。「非対応シンボル」と解釈しない。
