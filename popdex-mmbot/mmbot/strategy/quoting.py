"""Quote generation: fair value +- spread, skewed by inventory.

Analogy: a currency booth posts buy/sell rates around the interbank rate.
When its drawer fills up with euros it lowers both rates a touch so
customers buy euros from it rather than sell more - that's inventory skew.
"""
from __future__ import annotations

import math

from ..config import MarketCfg, QuoteCfg
from ..models import Quote, Side
from .humanizer import Humanizer


def round_to_tick(price: float, tick: float, side: Side) -> float:
    # bids round down, asks round up so we never accidentally cross
    n = price / tick
    n = math.floor(n) if side is Side.BUY else math.ceil(n)
    return float(f"{n * tick:.10g}")


class Quoter:
    def __init__(self, qcfg: QuoteCfg, mcfg: MarketCfg, human: Humanizer, max_pos_notional: float):
        self.q = qcfg
        self.m = mcfg
        self.h = human
        self.max_pos_notional = max_pos_notional

    def skew_bps(self, position_size: float, price: float) -> float:
        """Positive skew => shift quotes down (we are long, want to sell)."""
        if self.max_pos_notional <= 0:
            return 0.0
        ratio = (position_size * price) / self.max_pos_notional
        ratio = max(-1.0, min(1.0, ratio))
        return ratio * self.q.inventory_skew_bps

    def build(self, fair: float, position_size: float, funding: float = 0.0) -> list[Quote]:
        skew = self.skew_bps(position_size, fair)
        # Funding nudge: if we'd pay funding on a long, lean a little short.
        skew += max(-3.0, min(3.0, funding * 1e4 * 0.5))
        center = fair * (1 - skew / 1e4)
        want_bid, want_ask = self.h.quote_sides()
        quotes: list[Quote] = []
        pos_notional = position_size * fair
        for lvl in range(self.q.levels):
            half = self.q.base_spread_bps + lvl * self.q.level_step_bps + self.h.jitter_bps()
            half = max(half, 1.0)
            if want_bid and pos_notional < self.max_pos_notional:
                px = round_to_tick(center * (1 - half / 1e4), self.m.tick_size, Side.BUY)
                quotes.append(Quote(Side.BUY, px, self.h.order_size(px)))
            if want_ask and -pos_notional < self.max_pos_notional:
                px = round_to_tick(center * (1 + half / 1e4), self.m.tick_size, Side.SELL)
                quotes.append(Quote(Side.SELL, px, self.h.order_size(px)))
        # ensure min notional
        return [q for q in quotes if q.price * q.size >= self.m.min_notional_usd]

    def needs_requote(self, existing_price: float, desired_price: float) -> bool:
        return abs(existing_price - desired_price) / desired_price * 1e4 >= self.q.requote_threshold_bps
