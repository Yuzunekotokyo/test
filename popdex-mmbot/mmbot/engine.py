"""Main loop: read fair value -> risk gate -> maybe taker -> reconcile quotes."""
from __future__ import annotations

import asyncio
import logging
import signal

from .config import Config
from .exchange.base import ExchangeAdapter
from .journal import Journal
from .models import OrderType, Side
from .risk import RiskManager
from .strategy.humanizer import Humanizer
from .strategy.quoting import Quoter

log = logging.getLogger(__name__)


class Engine:
    def __init__(self, cfg: Config, exchange: ExchangeAdapter, feed):
        self.cfg = cfg
        self.ex = exchange
        self.feed = feed
        self.sym = cfg.market.symbol
        self.human = Humanizer(cfg.human, cfg.quote, cfg.market)
        self.quoter = Quoter(cfg.quote, cfg.market, self.human, cfg.risk.max_position_notional_usd)
        self.risk = RiskManager(cfg.risk)
        self.journal = Journal(cfg.log_dir)
        self._stop = asyncio.Event()

    # ---- lifecycle -------------------------------------------------------
    async def run(self) -> None:
        loop = asyncio.get_running_loop()
        for s in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(s, self._stop.set)
            except NotImplementedError:
                pass
        await self.feed.start()
        await self.ex.connect()
        log.info("engine started symbol=%s exchange=%s dry_run=%s",
                 self.sym, self.cfg.exchange.name, self.cfg.dry_run)
        try:
            while not self._stop.is_set():
                try:
                    await self.step()
                except Exception:  # noqa: BLE001
                    log.exception("step failed; pulling quotes")
                    await self._safe_cancel_all()
                wait = self.human.next_sleep()
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=wait)
                except asyncio.TimeoutError:
                    pass
        finally:
            await self._safe_cancel_all()
            await self.ex.close()
            await self.feed.stop()
            log.info("engine stopped")

    async def _safe_cancel_all(self) -> None:
        try:
            await self.ex.cancel_all(self.sym)
        except Exception:  # noqa: BLE001
            log.exception("cancel_all failed")

    # ---- one cycle -------------------------------------------------------
    async def step(self) -> None:
        fair = self.feed.price()
        if fair is None:
            return
        for f in await self.ex.poll_fills(self.sym):
            self.journal.fill(f)
            self.human.record_trade()
            log.info("FILL %s %s %.6g @ %.2f fee=%.4f maker=%s",
                     f.side.value, f.symbol, f.size, f.price, f.fee, f.is_maker)

        equity = await self.ex.equity()
        pos = await self.ex.position(self.sym)
        top = await self.ex.book_top(self.sym)
        funding = await self.ex.funding_rate(self.sym)
        self.risk.update_equity(equity)
        self.journal.snapshot(equity, pos.size, pos.entry_price, pos.unrealized(fair),
                              pos.realized_pnl, pos.fees_paid)

        ok, why = self.risk.may_quote(top, self.feed.age, pos, fair)
        if not ok:
            log.warning("not quoting: %s", why)
            await self._safe_cancel_all()
            return

        if self.human.on_break() or self.human.maybe_start_break():
            log.info("taking a break; cancelling resting orders")
            await self._safe_cancel_all()
            return
        if not self.human.should_quote():
            await self._safe_cancel_all()
            return

        await self._maybe_taker(fair, pos, equity, funding)
        await self._reconcile_quotes(fair, pos, funding)

    async def _maybe_taker(self, fair, pos, equity, funding) -> None:
        if not self.human.wants_taker() or not self.risk.order_rate_ok():
            return
        size = self.human.taker_size(fair)
        if self.human.taker_is_reduce_only():
            if abs(pos.size) < self.cfg.market.lot_size:
                return
            side = Side.SELL if pos.size > 0 else Side.BUY
            size = min(size, abs(pos.size))
            reduce_only = True
        else:
            side = Side.BUY if self.quoter.skew_bps(pos.size, fair) <= 0 else Side.SELL
            reduce_only = False
            if self.risk.funding_blocks_side(funding, side is Side.BUY):
                return
            if not self.risk.leverage_ok(pos, fair, equity, size * fair):
                return
        size = max(self.cfg.market.lot_size, round(size / self.cfg.market.lot_size) * self.cfg.market.lot_size)
        if size * fair < self.cfg.market.min_notional_usd:
            return
        log.info("TAKER %s %.6g reduce_only=%s", side.value, size, reduce_only)
        self.risk.note_order()
        await self.ex.place_order(self.sym, side, OrderType.MARKET, size, reduce_only=reduce_only, post_only=False)

    async def _reconcile_quotes(self, fair, pos, funding) -> None:
        desired = self.quoter.build(fair, pos.size, funding)
        desired = [q for q in desired if not self.risk.funding_blocks_side(funding, q.side is Side.BUY)]
        existing = await self.ex.open_orders(self.sym)
        import time
        now = time.time()
        for side in (Side.BUY, Side.SELL):
            want = [q for q in desired if q.side is side]
            have = [o for o in existing if o.side is side]
            # keep the first matching order if it's close enough and fresh
            keep = []
            for o in have:
                match = next((q for q in want if not self.quoter.needs_requote(o.price, q.price)), None)
                if match and now - o.created_at < self.cfg.quote.max_order_age_s:
                    keep.append(o)
                    want.remove(match)
                else:
                    await self.ex.cancel_order(o.id)
            for q in want:
                if not self.risk.order_rate_ok():
                    log.info("order rate cap reached; skipping %s", q.side.value)
                    break
                self.risk.note_order()
                o = await self.ex.place_order(self.sym, q.side, OrderType.LIMIT, q.size, q.price, post_only=True)
                if o.status == "rejected":
                    log.info("post-only rejected %s %.2f", q.side.value, q.price)
                else:
                    log.info("QUOTE %s %.6g @ %.2f", q.side.value, q.size, q.price)
