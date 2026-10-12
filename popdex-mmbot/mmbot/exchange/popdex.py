"""PopDEX adapter.

The public API base is https://api.popdex.ai/api/v1/public (confirmed from the
DefiLlama adapter). The private/trading endpoints, auth scheme (API key vs.
wallet signature) and rate limits could not be verified from this environment,
so every method marked TODO must be mapped to the real endpoint from
https://popdex.xyz/docs before `dry_run: false` is used.

Keep this file the *only* place that knows PopDEX's wire format.
"""
from __future__ import annotations

import time

import httpx

from ..models import BookTop, Fill, Order, OrderType, Position, Side
from .base import ExchangeAdapter


class PopdexExchange(ExchangeAdapter):
    PUBLIC = "/api/v1/public"
    PRIVATE = "/api/v1/private"   # TODO: confirm

    def __init__(self, rest_url: str, api_key: str, api_secret: str,
                 private_key: str = "", ws_url: str = ""):
        self.rest_url = rest_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.private_key = private_key
        self._client: httpx.AsyncClient | None = None
        self._last_fill_ts = time.time()

    # ---- lifecycle -------------------------------------------------------
    async def connect(self) -> None:
        self._client = httpx.AsyncClient(base_url=self.rest_url, timeout=10.0)
        # Fail fast if the public API is unreachable; this is a cheap sanity check.
        r = await self._client.get(f"{self.PUBLIC}/time")   # TODO: confirm endpoint
        r.raise_for_status()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    def _auth_headers(self, method: str, path: str, body: str = "") -> dict:
        """TODO: implement PopDEX request signing.

        Typical patterns on perp DEXs:
          * HMAC-SHA256 over f"{timestamp}{method}{path}{body}" with api_secret
          * EIP-712 typed-data signature with the wallet private key
        Fill in whichever the docs specify; never log the secret.
        """
        raise NotImplementedError("PopDEX auth not implemented - see docs")

    async def _get(self, path: str, **params):
        r = await self._client.get(path, params=params)
        r.raise_for_status()
        return r.json()

    async def _private(self, method: str, path: str, json: dict | None = None):
        import json as _json
        body = _json.dumps(json) if json else ""
        headers = self._auth_headers(method, path, body)
        r = await self._client.request(method, path, content=body or None, headers=headers)
        r.raise_for_status()
        return r.json()

    # ---- market data -----------------------------------------------------
    async def book_top(self, symbol: str) -> BookTop:
        # TODO: confirm path and field names (e.g. /orderbook?symbol=BTC-PERP&depth=1)
        d = await self._get(f"{self.PUBLIC}/orderbook", symbol=symbol, depth=1)
        return BookTop(bid=float(d["bids"][0][0]), ask=float(d["asks"][0][0]))

    async def funding_rate(self, symbol: str) -> float:
        # TODO: confirm (/funding or part of /ticker)
        d = await self._get(f"{self.PUBLIC}/funding", symbol=symbol)
        return float(d["fundingRate"])

    # ---- trading ---------------------------------------------------------
    async def place_order(self, symbol, side, type, size, price=None,
                          post_only=True, reduce_only=False) -> Order:
        payload = {
            "symbol": symbol,
            "side": side.value.upper(),
            "type": type.value.upper(),
            "size": str(size),
            "price": None if price is None else str(price),
            "postOnly": post_only,
            "reduceOnly": reduce_only,
        }
        d = await self._private("POST", f"{self.PRIVATE}/order", payload)   # TODO
        return Order(str(d["orderId"]), symbol, side, type, price, size,
                     post_only=post_only, status=d.get("status", "open").lower())

    async def cancel_order(self, order_id: str) -> None:
        await self._private("DELETE", f"{self.PRIVATE}/order/{order_id}")   # TODO

    async def cancel_all(self, symbol: str) -> None:
        await self._private("DELETE", f"{self.PRIVATE}/orders", {"symbol": symbol})  # TODO

    async def open_orders(self, symbol: str) -> list[Order]:
        d = await self._private("GET", f"{self.PRIVATE}/orders?symbol={symbol}")   # TODO
        return [
            Order(str(o["orderId"]), symbol, Side(o["side"].lower()),
                  OrderType(o["type"].lower()), float(o["price"]), float(o["size"]),
                  filled=float(o.get("filled", 0)), created_at=float(o["createdAt"]) / 1000)
            for o in d
        ]

    async def poll_fills(self, symbol: str) -> list[Fill]:
        d = await self._private("GET", f"{self.PRIVATE}/fills?symbol={symbol}&since={int(self._last_fill_ts*1000)}")  # TODO
        fills = []
        for f in d:
            ts = float(f["ts"]) / 1000
            fills.append(Fill(str(f["orderId"]), symbol, Side(f["side"].lower()),
                              float(f["price"]), float(f["size"]), float(f["fee"]),
                              bool(f["isMaker"]), ts))
            self._last_fill_ts = max(self._last_fill_ts, ts + 1e-3)
        return fills

    async def position(self, symbol: str) -> Position:
        d = await self._private("GET", f"{self.PRIVATE}/position?symbol={symbol}")   # TODO
        return Position(symbol, size=float(d.get("size", 0)),
                        entry_price=float(d.get("entryPrice", 0)),
                        realized_pnl=float(d.get("realizedPnl", 0)))

    async def equity(self) -> float:
        d = await self._private("GET", f"{self.PRIVATE}/account")   # TODO
        return float(d["equity"])
