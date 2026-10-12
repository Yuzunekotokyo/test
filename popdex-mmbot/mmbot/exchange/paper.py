"""Paper exchange: simulates a book around a reference price and fills
resting orders when the reference trades through them. Good enough to
validate pacing, inventory control and risk limits before going live."""
from __future__ import annotations

import itertools
import random
import time

from ..models import BookTop, Fill, Order, OrderType, Position, Side
from .base import ExchangeAdapter


class PaperExchange(ExchangeAdapter):
    def __init__(self, price_source, maker_fee_bps: float, taker_fee_bps: float,
                 equity_usd: float, spread_bps: float = 4.0, fill_prob: float = 0.35):
        self._price = price_source          # callable -> float | None
        self.maker_fee = maker_fee_bps / 1e4
        self.taker_fee = taker_fee_bps / 1e4
        self.spread = spread_bps / 1e4
        self.fill_prob = fill_prob          # chance a touched order fills per poll
        self._ids = itertools.count(1)
        self._orders: dict[str, Order] = {}
        self._pending_fills: list[Fill] = []
        self._pos: dict[str, Position] = {}
        self._cash = equity_usd
        self._funding = 0.0001

    async def connect(self) -> None:
        pass

    async def close(self) -> None:
        pass

    def _mid(self) -> float:
        p = self._price()
        if p is None:
            raise RuntimeError("no reference price yet")
        return p

    async def book_top(self, symbol: str) -> BookTop:
        m = self._mid()
        half = m * self.spread / 2
        return BookTop(bid=m - half, ask=m + half)

    async def funding_rate(self, symbol: str) -> float:
        self._funding += random.gauss(0, 0.00002)
        return max(-0.002, min(0.002, self._funding))

    def _pos_for(self, symbol: str) -> Position:
        return self._pos.setdefault(symbol, Position(symbol))

    async def place_order(self, symbol, side, type, size, price=None,
                          post_only=True, reduce_only=False) -> Order:
        oid = f"paper-{next(self._ids)}"
        if type is OrderType.MARKET:
            top = await self.book_top(symbol)
            px = top.ask if side is Side.BUY else top.bid
            order = Order(oid, symbol, side, type, None, size, filled=size,
                          post_only=False, status="filled")
            self._book_fill(order, px, is_maker=False)
            return order
        top = await self.book_top(symbol)
        crosses = (side is Side.BUY and price >= top.ask) or (side is Side.SELL and price <= top.bid)
        if post_only and crosses:
            return Order(oid, symbol, side, type, price, size, status="rejected")
        order = Order(oid, symbol, side, type, price, size, post_only=post_only)
        self._orders[oid] = order
        return order

    def _book_fill(self, order: Order, px: float, is_maker: bool) -> None:
        fee_rate = self.maker_fee if is_maker else self.taker_fee
        fee = order.size * px * fee_rate
        fill = Fill(order.id, order.symbol, order.side, px, order.size, fee, is_maker)
        self._pos_for(order.symbol).apply_fill(fill)
        self._cash -= fee
        self._pending_fills.append(fill)

    async def cancel_order(self, order_id: str) -> None:
        o = self._orders.pop(order_id, None)
        if o:
            o.status = "cancelled"

    async def cancel_all(self, symbol: str) -> None:
        for oid in [k for k, o in self._orders.items() if o.symbol == symbol]:
            await self.cancel_order(oid)

    async def open_orders(self, symbol: str) -> list[Order]:
        self._simulate_fills()
        return [o for o in self._orders.values() if o.symbol == symbol]

    def _simulate_fills(self) -> None:
        m = self._mid()
        for oid, o in list(self._orders.items()):
            # distance of the resting order from mid, in bps (negative = mid traded through it)
            dist = (o.price - m if o.side is Side.SELL else m - o.price) / m * 1e4
            if dist <= 0:
                p = self.fill_prob                       # mid traded through us
            elif dist <= self.spread * 1e4 * 2.5:
                p = self.fill_prob * 0.25 * (1 - dist / (self.spread * 1e4 * 2.5))  # taker flow sweeps nearby
            else:
                p = 0.0
            if random.random() < p:
                o.filled = o.size
                o.status = "filled"
                self._book_fill(o, o.price, is_maker=True)
                del self._orders[oid]

    async def poll_fills(self, symbol: str) -> list[Fill]:
        self._simulate_fills()
        out, self._pending_fills = self._pending_fills, []
        return out

    async def position(self, symbol: str) -> Position:
        return self._pos_for(symbol)

    async def equity(self) -> float:
        m = self._mid()
        return self._cash + sum(p.realized_pnl + p.unrealized(m) for p in self._pos.values())
