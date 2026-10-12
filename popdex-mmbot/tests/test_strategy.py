import random

from mmbot.config import HumanCfg, MarketCfg, QuoteCfg, RiskCfg
from mmbot.models import Fill, Position, Side
from mmbot.risk import RiskManager
from mmbot.strategy.humanizer import Humanizer
from mmbot.strategy.quoting import Quoter


def make(seed=1):
    h = Humanizer(HumanCfg(one_sided_prob=0.0), QuoteCfg(), MarketCfg(), random.Random(seed))
    return h, Quoter(QuoteCfg(), MarketCfg(), h, max_pos_notional=400)


def test_quotes_straddle_fair_and_never_cross():
    h, q = make()
    for _ in range(200):
        quotes = q.build(60000.0, 0.0)
        bids = [x.price for x in quotes if x.side is Side.BUY]
        asks = [x.price for x in quotes if x.side is Side.SELL]
        assert bids and asks
        assert max(bids) < 60000.0 < min(asks)


def test_long_inventory_shifts_quotes_down():
    h, q = make()
    flat = q.build(60000.0, 0.0)
    long = q.build(60000.0, 400 / 60000.0)   # at max position
    assert max(x.price for x in long if x.side is Side.SELL) < max(x.price for x in flat if x.side is Side.SELL)
    assert not any(x.side is Side.BUY for x in long)   # no more buying at cap


def test_sizes_vary_and_respect_lot():
    h, _ = make()
    sizes = {h.order_size(60000.0) for _ in range(100)}
    assert len(sizes) > 5
    for s in sizes:
        assert abs(round(s / 0.0001) * 0.0001 - s) < 1e-9
        assert 10 <= s * 60000 <= 150


def test_sleep_is_randomised():
    h, _ = make()
    waits = {round(h.next_sleep(), 2) for _ in range(20)}
    assert len(waits) > 10


def test_position_pnl_bookkeeping():
    p = Position("X")
    p.apply_fill(Fill("1", "X", Side.BUY, 100.0, 1.0, -0.01, True))
    p.apply_fill(Fill("2", "X", Side.BUY, 110.0, 1.0, -0.01, True))
    assert p.size == 2 and abs(p.entry_price - 105) < 1e-9
    p.apply_fill(Fill("3", "X", Side.SELL, 120.0, 3.0, 0.05, False))
    assert p.size == -1 and p.entry_price == 120.0
    assert abs(p.realized_pnl - 30.0) < 1e-9
    assert abs(p.fees_paid - 0.03) < 1e-9


def test_risk_halts_on_daily_loss():
    r = RiskManager(RiskCfg(max_daily_loss_usd=40))
    r.update_equity(800)
    r.update_equity(770)
    assert not r.halted
    r.update_equity(759)
    assert r.halted and "daily loss" in r.halted_reason


def test_order_rate_cap():
    r = RiskManager(RiskCfg(max_orders_per_minute=2))
    assert r.order_rate_ok(); r.note_order()
    assert r.order_rate_ok(); r.note_order()
    assert not r.order_rate_ok()
