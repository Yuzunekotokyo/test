"""Configuration loading. See config.example.yaml for every field."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class MarketCfg:
    symbol: str = "BTC-PERP"
    reference_symbol: str = "BTCUSDT"   # Binance symbol used as fair-value anchor
    tick_size: float = 0.1
    lot_size: float = 0.0001
    min_notional_usd: float = 10.0


@dataclass
class QuoteCfg:
    base_spread_bps: float = 6.0        # half-spread each side from fair value
    spread_jitter_bps: float = 2.0      # +- random noise so quotes aren't identical
    levels: int = 1                     # number of price levels per side
    level_step_bps: float = 4.0
    inventory_skew_bps: float = 8.0     # full skew at max position
    order_notional_min_usd: float = 25.0
    order_notional_max_usd: float = 120.0
    round_size_prob: float = 0.35       # chance to use a "human" round number
    requote_threshold_bps: float = 2.5  # move orders only if fair moved this much
    max_order_age_s: float = 240.0      # replace stale orders regardless


@dataclass
class HumanCfg:
    """Pacing so that activity looks like a discretionary trader, not a tick loop."""
    loop_interval_s: tuple[float, float] = (15.0, 75.0)   # random wait per cycle
    break_prob: float = 0.04                               # chance per cycle to pause
    break_duration_s: tuple[float, float] = (240.0, 1500.0)
    active_hours_local: tuple[int, int] = (8, 24)          # quote only inside window
    timezone: str = "Asia/Tokyo"
    off_hours_activity_prob: float = 0.15                  # occasional late-night trades
    target_trades_per_day: tuple[int, int] = (15, 50)
    taker_ratio: float = 0.2                                # share of trades sent as taker
    taker_reduce_only_prob: float = 0.7                     # taker mostly used to flatten
    taker_notional_usd: tuple[float, float] = (15.0, 60.0)
    one_sided_prob: float = 0.2                             # sometimes quote one side only


@dataclass
class RiskCfg:
    account_equity_usd: float = 800.0
    max_position_notional_usd: float = 400.0   # ~0.5x leverage on $800
    max_leverage: float = 1.5
    max_daily_loss_usd: float = 40.0           # 5% of equity -> stop for the day
    max_drawdown_usd: float = 80.0             # 10% -> hard stop
    stale_price_s: float = 20.0                # fair value older than this = pull quotes
    max_spread_bps_to_quote: float = 60.0      # don't quote into a broken book
    funding_rate_abs_limit: float = 0.001      # pull same-side quotes if funding extreme
    max_orders_per_minute: int = 6


@dataclass
class ExchangeCfg:
    name: str = "paper"                 # paper | popdex
    rest_url: str = "https://api.popdex.ai"
    ws_url: str = ""
    api_key: str = ""
    api_secret: str = ""
    private_key: str = ""               # for wallet-signed orders, if PopDEX requires
    maker_fee_bps: float = -1.0         # negative = rebate
    taker_fee_bps: float = 4.0


@dataclass
class Config:
    market: MarketCfg = field(default_factory=MarketCfg)
    quote: QuoteCfg = field(default_factory=QuoteCfg)
    human: HumanCfg = field(default_factory=HumanCfg)
    risk: RiskCfg = field(default_factory=RiskCfg)
    exchange: ExchangeCfg = field(default_factory=ExchangeCfg)
    log_dir: str = "logs"
    dry_run: bool = True                # paper exchange unless explicitly disabled


def _merge(dc, data: dict):
    for k, v in (data or {}).items():
        if not hasattr(dc, k):
            raise KeyError(f"unknown config key: {k}")
        cur = getattr(dc, k)
        if isinstance(cur, tuple) and isinstance(v, list):
            v = tuple(v)
        setattr(dc, k, v)
    return dc


def load_config(path: str | Path) -> Config:
    raw = yaml.safe_load(Path(path).read_text()) or {}
    cfg = Config()
    for section in ("market", "quote", "human", "risk", "exchange"):
        _merge(getattr(cfg, section), raw.get(section, {}))
    cfg.log_dir = raw.get("log_dir", cfg.log_dir)
    cfg.dry_run = bool(raw.get("dry_run", cfg.dry_run))
    if not cfg.dry_run and cfg.exchange.name == "paper":
        raise ValueError("dry_run=false requires exchange.name != paper")
    return cfg
