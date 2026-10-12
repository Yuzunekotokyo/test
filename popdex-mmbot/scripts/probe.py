#!/usr/bin/env python3
"""Read-only probe to confirm the REST paths / field names before trading.

    python scripts/probe.py --config config.yaml

Prints raw responses for instruments, orderbook, tickers, agents, positions,
balance and open orders. Paste the output back if something looks off and the
adapter's parsing can be adjusted. Sends no transactions.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mmbot.config import load_config  # noqa: E402
from mmbot.exchange.popdex import MAINNET, TESTNET  # noqa: E402


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    a = ap.parse_args()
    cfg = load_config(a.config)
    p = cfg.popdex
    net = MAINNET if p.network == "mainnet" else TESTNET
    base = (cfg.exchange.rest_url or net["rest_url"]).rstrip("/")
    sym = cfg.market.symbol
    addr = p.main_address

    checks = [
        ("instruments", p.rest_paths["instruments"], {"category": "Futures"}),
        ("orderbook", p.rest_paths["orderbook"], {"category": "Futures", "symbol": sym, "limit": 5}),
        ("tickers", p.rest_paths["tickers"], {"category": "Futures", "symbol": sym}),
        ("funding", p.rest_paths["funding"], {"category": "Futures", "symbol": sym}),
    ]
    if addr:
        checks += [
            ("agents", p.rest_paths["agents"].format(addr=addr), {}),
            ("positions", p.rest_paths["positions"].format(addr=addr), {"category": "Futures"}),
            ("balance", p.rest_paths["balance"].format(addr=addr), {}),
            ("open_orders", p.rest_paths["open_orders"].format(addr=addr), {"category": "Futures", "symbol": sym}),
        ]
    async with httpx.AsyncClient(base_url=base, timeout=15) as c:
        for name, path, params in checks:
            try:
                r = await c.get(path, params=params)
                body = r.text
                try:
                    body = json.dumps(r.json(), indent=1, ensure_ascii=False)
                except ValueError:
                    pass
                rl = {k: v for k, v in r.headers.items() if k.lower().startswith("x-ratelimit")}
                print(f"\n=== {name}  GET {path} {params}  -> {r.status_code} {rl}\n{body[:2500]}")
            except Exception as e:  # noqa: BLE001
                print(f"\n=== {name}  GET {path}  -> ERROR {e}")


if __name__ == "__main__":
    asyncio.run(main())
