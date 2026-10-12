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
        from mmbot.exchange.popdex import PopdexExchange, PopdexParams
        p, e = cfg.popdex, cfg.exchange
        key = p.agent_private_key or os.getenv("POPDEX_AGENT_PRIVATE_KEY", "")
        main_addr = p.main_address
        if not key and os.path.exists(p.agent_key_file):
            import configparser
            ini = configparser.ConfigParser(); ini.read(p.agent_key_file)
            key = ini["DEFAULT"].get("agent_private_key", "")
            main_addr = main_addr or ini["DEFAULT"].get("main_address", "")
            if ini["DEFAULT"].get("network", p.network) != p.network:
                raise SystemExit(f"{p.agent_key_file} is for {ini['DEFAULT'].get('network')}, config says {p.network}")
        params = PopdexParams(main_address=main_addr, agent_private_key=key, network=p.network,
                              symbol_id=p.symbol_id, price_decimals=p.price_decimals,
                              qty_decimals=p.qty_decimals, enum_limit=p.enum_limit,
                              enum_market=p.enum_market, enum_buy=p.enum_buy, enum_sell=p.enum_sell,
                              enum_post_only=p.enum_post_only, enum_ioc=p.enum_ioc, enum_gtc=p.enum_gtc,
                              cancel_abi=p.cancel_abi, gas_limit=p.gas_limit, rest_paths=p.rest_paths)
        ex = PopdexExchange(params, cfg.market.symbol, e.rest_url, e.rpc_url, e.ws_url)
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
