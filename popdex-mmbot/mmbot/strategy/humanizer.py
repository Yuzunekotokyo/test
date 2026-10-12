"""Pacing and sizing decisions that keep the bot's footprint irregular.

Why this exists: a loop that re-quotes every 500 ms with identical sizes is
trivially distinguishable from a trader. Randomised intervals, breaks, an
active-hours window, varied sizes and a share of taker trades make the
order flow look like someone clicking - while the *economics* stay with the
quoting logic in quoting.py. Nothing here hides positions or wash-trades.
"""
from __future__ import annotations

import math
import random
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from ..config import HumanCfg, MarketCfg, QuoteCfg


class Humanizer:
    def __init__(self, hcfg: HumanCfg, qcfg: QuoteCfg, mcfg: MarketCfg, rng: random.Random | None = None):
        self.h = hcfg
        self.q = qcfg
        self.m = mcfg
        self.rng = rng or random.Random()
        self._break_until = 0.0
        self._day = None
        self._daily_budget = 0
        self._trades_today = 0
        self._pace_factor = 1.0

    # ---- time ------------------------------------------------------------
    def now_local(self) -> datetime:
        return datetime.now(ZoneInfo(self.h.timezone))

    def _roll_day(self) -> None:
        d = self.now_local().date()
        if d != self._day:
            self._day = d
            lo, hi = self.h.target_trades_per_day
            self._daily_budget = self.rng.randint(lo, hi)
            self._trades_today = 0
            # a "mood" for the day: some days quote tighter/faster
            self._pace_factor = self.rng.uniform(0.75, 1.3)

    def record_trade(self) -> None:
        self._roll_day()
        self._trades_today += 1

    def trades_today(self) -> int:
        self._roll_day()
        return self._trades_today

    def within_active_hours(self) -> bool:
        self._roll_day()
        h = self.now_local().hour
        start, end = self.h.active_hours_local
        if start <= h < end:
            return True
        # low-probability off-hours activity, sticky for a while via break timer
        return self.rng.random() < self.h.off_hours_activity_prob

    def on_break(self) -> bool:
        return time.time() < self._break_until

    def maybe_start_break(self) -> bool:
        if self.rng.random() < self.h.break_prob:
            lo, hi = self.h.break_duration_s
            self._break_until = time.time() + self.rng.uniform(lo, hi)
            return True
        return False

    def next_sleep(self) -> float:
        lo, hi = self.h.loop_interval_s
        # log-normal-ish so most waits are short but some are long
        base = self.rng.uniform(lo, hi)
        return base * self._pace_factor * self.rng.lognormvariate(0, 0.35)

    def budget_exhausted(self) -> bool:
        self._roll_day()
        return self._trades_today >= self._daily_budget

    def should_quote(self) -> bool:
        return self.within_active_hours() and not self.on_break() and not self.budget_exhausted()

    # ---- sizing ----------------------------------------------------------
    def order_size(self, price: float, lo_usd: float | None = None, hi_usd: float | None = None) -> float:
        lo = lo_usd if lo_usd is not None else self.q.order_notional_min_usd
        hi = hi_usd if hi_usd is not None else self.q.order_notional_max_usd
        # triangular: cluster around a comfortable size, occasional bigger clips
        usd = self.rng.triangular(lo, hi, lo + (hi - lo) * 0.35)
        size = usd / price
        lot = self.m.lot_size
        if self.rng.random() < self.q.round_size_prob:
            # humans like round numbers: snap to 1/2/5 x power of ten of the lot
            mag = 10 ** math.floor(math.log10(max(size, lot)))
            size = min([1, 2, 5], key=lambda k: abs(k * mag - size)) * mag
        size = max(lot, round(size / lot) * lot)
        return float(f"{size:.10g}")

    def quote_sides(self) -> tuple[bool, bool]:
        """(quote_bid, quote_ask) - sometimes only one side."""
        if self.rng.random() < self.h.one_sided_prob:
            return (True, False) if self.rng.random() < 0.5 else (False, True)
        return True, True

    def jitter_bps(self) -> float:
        return self.rng.uniform(-self.q.spread_jitter_bps, self.q.spread_jitter_bps)

    # ---- taker -----------------------------------------------------------
    def wants_taker(self) -> bool:
        return self.rng.random() < self.h.taker_ratio

    def taker_is_reduce_only(self) -> bool:
        return self.rng.random() < self.h.taker_reduce_only_prob

    def taker_size(self, price: float) -> float:
        lo, hi = self.h.taker_notional_usd
        return self.order_size(price, lo, hi)
