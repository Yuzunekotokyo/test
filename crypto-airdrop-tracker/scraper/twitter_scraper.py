"""
Perp DEX Airdrop Tracker - X (Twitter) API Scraper

X APIを使ってPerp DEXのエアドロップ関連ツイートを取得し、
JSON形式で保存するスクリプト。

使い方:
    # 環境変数にBearer Tokenを設定
    export TWITTER_BEARER_TOKEN="your_bearer_token_here"

    # 全プロトコルのツイートを取得
    python twitter_scraper.py

    # 特定のプロトコルのみ
    python twitter_scraper.py --protocol hyperliquid

    # 出力先を指定
    python twitter_scraper.py --output ../data/tweets.json
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
PROTOCOLS_FILE = DATA_DIR / "protocols.json"

BASE_URL = "https://api.twitter.com/2/tweets/search/recent"


def get_bearer_token():
    """環境変数からBearer Tokenを取得"""
    token = os.environ.get("TWITTER_BEARER_TOKEN")
    if not token:
        print("エラー: TWITTER_BEARER_TOKEN 環境変数を設定してください")
        print("  export TWITTER_BEARER_TOKEN='your_bearer_token_here'")
        sys.exit(1)
    return token


def load_protocols(protocol_id=None):
    """protocols.jsonからプロトコル情報を読み込み"""
    with open(PROTOCOLS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    protocols = data["protocols"]
    if protocol_id:
        protocols = [p for p in protocols if p["id"] == protocol_id]
        if not protocols:
            print(f"エラー: プロトコル '{protocol_id}' が見つかりません")
            sys.exit(1)

    return protocols


def search_tweets(query, bearer_token, max_results=10):
    """X APIでツイートを検索"""
    params = (
        f"?query={query}"
        f"&max_results={max_results}"
        f"&tweet.fields=created_at,public_metrics,author_id,lang"
        f"&expansions=author_id"
        f"&user.fields=name,username,public_metrics"
    )

    url = BASE_URL + params
    req = Request(url)
    req.add_header("Authorization", f"Bearer {bearer_token}")
    req.add_header("Content-Type", "application/json")

    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"  HTTP Error {e.code}: {error_body[:200]}")
        if e.code == 429:
            print("  レート制限に達しました。15分後に再試行してください。")
        return None
    except URLError as e:
        print(f"  接続エラー: {e.reason}")
        return None


def format_tweet(tweet, users_map):
    """ツイートデータを整形"""
    user = users_map.get(tweet.get("author_id"), {})
    metrics = tweet.get("public_metrics", {})

    return {
        "id": tweet.get("id"),
        "text": tweet.get("text"),
        "created_at": tweet.get("created_at"),
        "lang": tweet.get("lang"),
        "author": {
            "name": user.get("name", "Unknown"),
            "username": user.get("username", "unknown"),
            "followers": user.get("public_metrics", {}).get("followers_count", 0),
        },
        "metrics": {
            "likes": metrics.get("like_count", 0),
            "retweets": metrics.get("retweet_count", 0),
            "replies": metrics.get("reply_count", 0),
            "impressions": metrics.get("impression_count", 0),
        },
    }


def calculate_sentiment(tweets):
    """簡易的なセンチメント分析（エンゲージメント率ベース）"""
    if not tweets:
        return {"score": 0, "label": "データなし", "tweet_count": 0}

    total_engagement = 0
    total_impressions = 0

    for tweet in tweets:
        m = tweet["metrics"]
        total_engagement += m["likes"] + m["retweets"] * 2 + m["replies"]
        total_impressions += m["impressions"] if m["impressions"] > 0 else 1

    avg_engagement = total_engagement / len(tweets)

    if avg_engagement > 100:
        label = "非常にポジティブ"
        score = 5
    elif avg_engagement > 50:
        label = "ポジティブ"
        score = 4
    elif avg_engagement > 20:
        label = "やや注目"
        score = 3
    elif avg_engagement > 5:
        label = "普通"
        score = 2
    else:
        label = "低関心"
        score = 1

    return {
        "score": score,
        "label": label,
        "tweet_count": len(tweets),
        "avg_engagement": round(avg_engagement, 1),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Perp DEX Airdrop Tracker - X API Scraper"
    )
    parser.add_argument(
        "--protocol", type=str, help="特定のプロトコルIDのみ取得"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DATA_DIR / "tweets.json"),
        help="出力ファイルパス (デフォルト: data/tweets.json)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="プロトコルあたりの最大ツイート数 (デフォルト: 10)",
    )
    parser.add_argument(
        "--no-token-only",
        action="store_true",
        help="トークン未発行のプロトコルのみ取得",
    )
    args = parser.parse_args()

    bearer_token = get_bearer_token()
    protocols = load_protocols(args.protocol)

    if args.no_token_only:
        protocols = [p for p in protocols if not p.get("hasToken")]

    print(f"=== Perp DEX Airdrop Tracker - X API Scraper ===")
    print(f"対象プロトコル数: {len(protocols)}")
    print(f"出力先: {args.output}")
    print()

    results = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "protocol_count": len(protocols),
        "protocols": {},
    }

    for i, protocol in enumerate(protocols):
        name = protocol["name"]
        query = protocol.get("xSearchQuery", f"{name} airdrop")
        print(f"[{i + 1}/{len(protocols)}] {name} ... ", end="", flush=True)

        from urllib.parse import quote

        data = search_tweets(quote(query), bearer_token, args.max_results)

        if data and data.get("data"):
            users_map = {}
            if data.get("includes", {}).get("users"):
                for user in data["includes"]["users"]:
                    users_map[user["id"]] = user

            tweets = [format_tweet(t, users_map) for t in data["data"]]
            sentiment = calculate_sentiment(tweets)

            results["protocols"][protocol["id"]] = {
                "name": name,
                "query": query,
                "tweet_count": len(tweets),
                "sentiment": sentiment,
                "tweets": tweets,
            }
            print(
                f"{len(tweets)}件取得 "
                f"(センチメント: {sentiment['label']}, "
                f"平均エンゲージメント: {sentiment['avg_engagement']})"
            )
        else:
            results["protocols"][protocol["id"]] = {
                "name": name,
                "query": query,
                "tweet_count": 0,
                "sentiment": calculate_sentiment([]),
                "tweets": [],
            }
            print("取得失敗またはツイートなし")

        # Rate limit対策: 1秒待機
        if i < len(protocols) - 1:
            time.sleep(1)

    # 結果を保存
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print()
    print(f"=== 完了 ===")
    print(f"取得成功: {sum(1 for p in results['protocols'].values() if p['tweet_count'] > 0)}")
    print(f"取得失敗: {sum(1 for p in results['protocols'].values() if p['tweet_count'] == 0)}")
    print(f"結果保存先: {output_path}")


if __name__ == "__main__":
    main()
