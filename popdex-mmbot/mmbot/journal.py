"""Append-only CSV journal of fills and periodic snapshots."""
from __future__ import annotations

import csv
import time
from pathlib import Path

from .models import Fill


class Journal:
    def __init__(self, log_dir: str):
        d = Path(log_dir)
        d.mkdir(parents=True, exist_ok=True)
        self._fills = d / "fills.csv"
        self._snaps = d / "snapshots.csv"
        if not self._fills.exists():
            self._fills.write_text("ts,symbol,side,price,size,fee,is_maker,order_id\n")
        if not self._snaps.exists():
            self._snaps.write_text("ts,equity,position,entry,unrealized,realized,fees,maker_fills,taker_fills\n")
        self.maker_fills = 0
        self.taker_fills = 0

    def fill(self, f: Fill) -> None:
        if f.is_maker:
            self.maker_fills += 1
        else:
            self.taker_fills += 1
        with self._fills.open("a", newline="") as fh:
            csv.writer(fh).writerow([f"{f.ts:.3f}", f.symbol, f.side.value, f.price, f.size,
                                     f"{f.fee:.6f}", int(f.is_maker), f.order_id])

    def snapshot(self, equity: float, pos_size: float, entry: float, unreal: float,
                 realized: float, fees: float) -> None:
        with self._snaps.open("a", newline="") as fh:
            csv.writer(fh).writerow([f"{time.time():.0f}", f"{equity:.2f}", pos_size, entry,
                                     f"{unreal:.2f}", f"{realized:.2f}", f"{fees:.4f}",
                                     self.maker_fills, self.taker_fills])
