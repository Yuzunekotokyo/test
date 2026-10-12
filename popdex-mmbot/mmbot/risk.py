"""Risk gate. Every decision to quote or take passes through here first.

Think of it as the circuit breaker in a house: the strategy can ask for
anything, but if a limit trips the power goes off until a human resets it."""
from __future__ import annotations

import logging
import time
from collections import deque
from datetime import date

from .config import RiskCfg
from .models import BookTop, Position

log = logging.getLogger(__name__)


class RiskManager:
    def __init__(self, cfg: RiskCfg):
        self.c = cfg
        self.start_equity: float | None = None
        self.day_start_equity: float | None = None
        self.peak_equity: float | None = None
        self._day: date | None = None
        self.halted_reason: str | None = None
        self._order_times: deque[float] = deque()

    def update_equity(self, equity: float) -> None:
        today = date.today()
        if self.start_equity is None:
            self.start_equity = equity
        if self._day != today:
            self._day = today
            self.day_start_equity = equity
        self.peak_equity = max(self.peak_equity or equity, equity)

        if self.day_start_equity - equity >= self.c.max_daily_loss_usd:
            self.halt(f"daily loss limit hit ({self.day_start_equity - equity:.2f} USD)")
        if self.peak_equity - equity >= self.c.max_drawdown_usd:
            self.halt(f"max drawdown hit ({self.peak_equity - equity:.2f} USD)")

    def halt(self, reason: str) -> None:
        if not self.halted_reason:
            log.error("RISK HALT: %s", reason)
        self.halted_reason = reason

    @property
    def halted(self) -> bool:
        return self.halted_reason is not None

    def may_quote(self, top: BookTop, price_age_s: float, position: Position, mark: float) -> tuple[bool, str]:
        if self.halted:
            return False, self.halted_reason
        if price_age_s > self.c.stale_price_s:
            return False, f"reference price stale ({price_age_s:.0f}s)"
        if top.spread_bps > self.c.max_spread_bps_to_quote:
            return False, f"book spread too wide ({top.spread_bps:.1f} bps)"
        if abs(position.size) * mark > self.c.max_position_notional_usd * 1.25:
            return False, "position above hard cap"
        return True, "ok"

    def funding_blocks_side(self, funding: float, side_is_buy: bool) -> bool:
        """Extreme positive funding punishes longs; don't add long exposure then."""
        if abs(funding) < self.c.funding_rate_abs_limit:
            return False
        return (funding > 0) == side_is_buy

    def order_rate_ok(self) -> bool:
        now = time.time()
        while self._order_times and now - self._order_times[0] > 60:
            self._order_times.popleft()
        return len(self._order_times) < self.c.max_orders_per_minute

    def note_order(self) -> None:
        self._order_times.append(time.time())

    def leverage_ok(self, position: Position, mark: float, equity: float, extra_notional: float = 0.0) -> bool:
        if equity <= 0:
            return False
        return (abs(position.size) * mark + extra_notional) / equity <= self.c.max_leverage
