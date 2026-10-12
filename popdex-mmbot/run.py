#!/usr/bin/env python3
"""Entry point.  `python run.py --config config.yaml`"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mmbot.config import load_config  # noqa: E402
from mmbot.engine import Engine  # noqa: E402
from mmbot.exchange.paper import PaperExchange  # noqa: E402
from mmbot.feeds.binance import BinanceFeed, RandomWalkFeed  # noqa: E402


def build(cfg, offline: bool):
    feed = RandomWalkFeed() if offline else BinanceFeed(cfg.market.reference_symbol)
    if cfg.dry_run or cfg.exchange.name == "paper":
        ex = PaperExchange(feed.price, cfg.exchange.maker_fee_bps, cfg.exchange.taker_fee_bps,
                           cfg.risk.account_equity_usd)
    elif cfg.exchange.name == "popdex":
        from mmbot.exchange.popdex import PopdexExchange
        e = cfg.exchange
        ex = PopdexExchange(e.rest_url, e.api_key or os.getenv("POPDEX_API_KEY", ""),
                            e.api_secret or os.getenv("POPDEX_API_SECRET", ""),
                            e.private_key or os.getenv("POPDEX_PRIVATE_KEY", ""), e.ws_url)
    else:
        raise SystemExit(f"unknown exchange {cfg.exchange.name}")
    return Engine(cfg, ex, feed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--offline", action="store_true", help="random-walk price instead of Binance")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = load_config(a.config)
    if not cfg.dry_run:
        print("*** LIVE MODE: real orders will be sent. Ctrl-C within 5s to abort. ***")
        import time
        time.sleep(5)
    asyncio.run(build(cfg, a.offline).run())


if __name__ == "__main__":
    main()
