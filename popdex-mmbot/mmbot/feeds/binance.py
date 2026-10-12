"""Reference (fair-value) price from Binance's public book ticker.

Polling REST keeps dependencies minimal; swap for the websocket stream later
if latency matters. The bot never trades on Binance."""
from __future__ import annotations

import asyncio
import logging
import time

import httpx

log = logging.getLogger(__name__)


class BinanceFeed:
    URL = "https://api.binance.com/api/v3/ticker/bookTicker"

    def __init__(self, symbol: str, interval_s: float = 1.0):
        self.symbol = symbol
        self.interval = interval_s
        self.mid: float | None = None
        self.updated_at: float = 0.0
        self._task: asyncio.Task | None = None

    def price(self) -> float | None:
        return self.mid

    @property
    def age(self) -> float:
        return time.time() - self.updated_at if self.updated_at else float("inf")

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run())
        # wait for the first tick so callers never start with None
        for _ in range(100):
            if self.mid is not None:
                return
            await asyncio.sleep(0.1)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()

    async def _run(self) -> None:
        async with httpx.AsyncClient(timeout=5.0) as c:
            while True:
                try:
                    r = await c.get(self.URL, params={"symbol": self.symbol})
                    r.raise_for_status()
                    d = r.json()
                    self.mid = (float(d["bidPrice"]) + float(d["askPrice"])) / 2
                    self.updated_at = time.time()
                except Exception as e:  # noqa: BLE001
                    log.warning("binance feed error: %s", e)
                await asyncio.sleep(self.interval)


class RandomWalkFeed:
    """Offline stand-in for tests / demos when there is no network."""

    def __init__(self, start: float = 60000.0, vol_bps_per_tick: float = 3.0, interval_s: float = 1.0):
        self.mid = start
        self.vol = vol_bps_per_tick / 1e4
        self.interval = interval_s
        self.updated_at = time.time()
        self._task = None

    def price(self):
        return self.mid

    @property
    def age(self):
        return time.time() - self.updated_at

    async def start(self):
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        if self._task:
            self._task.cancel()

    async def _run(self):
        import random
        while True:
            self.mid *= 1 + random.gauss(0, self.vol)
            self.updated_at = time.time()
            await asyncio.sleep(self.interval)
