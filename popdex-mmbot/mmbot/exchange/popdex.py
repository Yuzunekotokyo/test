"""PopDEX adapter.

PopDEX is not a REST exchange: placing/cancelling orders means sending a
transaction to the *Order precompile* on its own chain (chainId 2184), signed
by an Agent Key that the main wallet has approved. REST and WebSocket are
read-only. See docs/popdex-api-notes.md for the source of every constant.

Known-unknowns (not in the reference article) are pulled from PopdexParams so
they can be fixed from config once confirmed on testnet:
  * numeric values of the orderParams enums
  * price / qty fixed-point scale
  * cancelOrder ABI
  * exact REST read paths
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field

import httpx
from eth_account import Account
from web3 import Web3

from ..models import BookTop, Fill, Order, OrderType, Position, Side
from .base import ExchangeAdapter

log = logging.getLogger(__name__)

ORDER_PRECOMPILE = "0x0000000000000000000000000000000000001000"
ACCOUNT_PRECOMPILE = "0x0000000000000000000000000000000000001008"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

MAINNET = dict(rpc_url="https://app.popdex.xyz/api/v1/web3/rpc", chain_id=2184,
               rest_url="https://api.popdex.xyz", ws_url="wss://ws.popdex.xyz/v1/ws/public")
TESTNET = dict(rpc_url="https://testnet-app.popdex.xyz/api/v1/web3/rpc", chain_id=34952,
               rest_url="https://testnet-api.popdex.xyz", ws_url="wss://testnet-ws.popdex.xyz/v1/ws/public")

ORDER_ABI = [
    {"type": "function", "name": "placeOrder", "stateMutability": "nonpayable", "outputs": [],
     "inputs": [
         {"name": "main", "type": "address"}, {"name": "clientOrderId", "type": "bytes32"},
         {"name": "symbolId", "type": "uint16"}, {"name": "orderParams", "type": "bytes32"},
         {"name": "price", "type": "uint256"}, {"name": "qty", "type": "uint256"},
         {"name": "slippage", "type": "uint256"}, {"name": "builder", "type": "address"},
         {"name": "builderFee", "type": "uint256"}]},
]


@dataclass
class PopdexParams:
    """Wire-format knobs. Values marked VERIFY are educated guesses."""
    main_address: str = ""
    agent_private_key: str = ""
    network: str = "mainnet"                 # mainnet | testnet
    symbol_id: int | None = None             # resolved from REST instruments if None
    price_decimals: int = 18                 # VERIFY
    qty_decimals: int = 18                   # VERIFY
    enum_limit: int = 0                      # VERIFY orderType
    enum_market: int = 1                     # VERIFY
    enum_buy: int = 0                        # VERIFY side
    enum_sell: int = 1                       # VERIFY
    enum_post_only: int = 1                  # VERIFY timeInForce
    enum_ioc: int = 2                        # VERIFY
    enum_gtc: int = 0                        # VERIFY
    # VERIFY: cancelOrder signature. Edit this one line once the docs confirm it.
    cancel_abi: str = "cancelOrder(address main,uint16 symbolId,bytes32 clientOrderId)"
    gas_limit: int = 2_000_000
    rest_paths: dict = field(default_factory=lambda: {   # VERIFY each
        "instruments": "/api/v1/public/market/instruments",
        "orderbook": "/api/v1/public/market/orderbook",
        "tickers": "/api/v1/public/market/tickers",
        "funding": "/api/v1/public/market/funding",
        "open_orders": "/api/v1/account/{addr}/orders",
        "positions": "/api/v1/account/{addr}/positions",
        "balance": "/api/v1/account/{addr}/balance",
        "agents": "/api/v1/account/{addr}/agents",
    })


def pack_order_params(category: int, order_type: int, side: int, tif: int,
                      market_unit: int = 0, bbo: int = 0, reduce_only: bool = False,
                      position_side: int = 0, stp: int = 0) -> bytes:
    b = bytearray(32)
    b[0], b[1], b[2], b[3], b[4] = category, order_type, side, tif, market_unit
    b[5], b[6], b[7], b[9] = bbo, int(reduce_only), position_side, stp
    return bytes(b)


def client_order_id(prefix: str = "mm") -> bytes:
    """Alphanumeric + hyphen only ('_' and '.' revert on chain)."""
    s = f"{prefix}-{int(time.time() * 1000)}"
    s = re.sub(r"[^A-Za-z0-9-]", "", s)[:32]
    return s.encode().ljust(32, b"\0")


class NonceSource:
    """Millisecond timestamp nonce, forced strictly increasing."""

    def __init__(self):
        self._last = 0

    def next(self) -> int:
        n = int(time.time() * 1000)
        if n <= self._last:
            n = self._last + 1
        self._last = n
        return n


class PopdexExchange(ExchangeAdapter):
    def __init__(self, params: PopdexParams, symbol: str, rest_url: str = "", rpc_url: str = "",
                 ws_url: str = "", chain_id: int | None = None):
        net = MAINNET if params.network == "mainnet" else TESTNET
        self.p = params
        self.symbol = symbol
        self.rest_url = (rest_url or net["rest_url"]).rstrip("/")
        self.rpc_url = rpc_url or net["rpc_url"]
        self.ws_url = ws_url or net["ws_url"]
        self.chain_id = chain_id or net["chain_id"]
        if not params.main_address or not params.agent_private_key:
            raise ValueError("popdex.main_address and popdex.agent_private_key are required")
        self.main = Web3.to_checksum_address(params.main_address)
        self.agent = Account.from_key(params.agent_private_key)
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 15}))
        self.order_contract = self.w3.eth.contract(address=ORDER_PRECOMPILE, abi=ORDER_ABI)
        self.cancel_selector = Web3.keccak(text=self.p.cancel_abi)[:4]
        self._nonce = NonceSource()
        self._tx_lock = asyncio.Lock()
        self._http: httpx.AsyncClient | None = None
        self._ws_task: asyncio.Task | None = None
        self._fills: asyncio.Queue[Fill] = asyncio.Queue()
        self._local_orders: dict[str, Order] = {}    # clientOrderId -> Order we sent
        self.symbol_id: int | None = params.symbol_id
        self.tick_size: float | None = None
        self.lot_size: float | None = None

    # ---- lifecycle -------------------------------------------------------
    async def connect(self) -> None:
        self._http = httpx.AsyncClient(base_url=self.rest_url, timeout=10.0)
        await self._check_agent_approved()
        if self.symbol_id is None:
            await self._resolve_symbol()
        self._ws_task = asyncio.create_task(self._ws_loop())
        log.info("popdex connected: network=%s main=%s agent=%s symbol=%s id=%s",
                 self.p.network, self.main, self.agent.address, self.symbol, self.symbol_id)

    async def close(self) -> None:
        if self._ws_task:
            self._ws_task.cancel()
        if self._http:
            await self._http.aclose()

    async def _check_agent_approved(self) -> None:
        d = await self._get(self.p.rest_paths["agents"].format(addr=self.main))
        agents = d.get("data", d) if isinstance(d, dict) else d
        found = any(self.agent.address.lower() in json.dumps(a).lower() for a in (agents or []))
        if not found:
            raise RuntimeError(f"agent {self.agent.address} is not approved for {self.main}; "
                               f"run scripts/approve_agent.py first")

    async def _resolve_symbol(self) -> None:
        d = await self._get(self.p.rest_paths["instruments"], category="Futures")
        rows = d.get("data", d) if isinstance(d, dict) else d
        if isinstance(rows, dict):
            rows = rows.get("list", rows.get("instruments", []))
        for r in rows or []:
            if str(r.get("symbol", "")).upper() == self.symbol.upper():
                self.symbol_id = int(r.get("symbolId", r.get("id")))
                self.tick_size = float(r.get("tickSize", r.get("priceStep", 0)) or 0) or None
                self.lot_size = float(r.get("lotSize", r.get("qtyStep", 0)) or 0) or None
                return
        raise RuntimeError(f"symbol {self.symbol} not found in instruments; set popdex.symbol_id manually")

    # ---- REST reads ------------------------------------------------------
    async def _get(self, path: str, **params):
        r = await self._http.get(path, params=params)
        r.raise_for_status()
        d = r.json()
        if isinstance(d, dict) and d.get("code") not in (None, 0, "0", 200):
            raise RuntimeError(f"popdex rest error {d.get('code')}: {d.get('msg') or d.get('message')}")
        return d

    @staticmethod
    def _rows(d):
        if isinstance(d, dict):
            d = d.get("data", d)
        if isinstance(d, dict):
            for k in ("list", "orders", "positions", "result"):
                if k in d:
                    return d[k]
        return d

    async def book_top(self, symbol: str) -> BookTop:
        d = await self._get(self.p.rest_paths["orderbook"], category="Futures", symbol=symbol, limit=1)
        data = d.get("data", d)
        bids, asks = data.get("b", data.get("bids")), data.get("a", data.get("asks"))
        return BookTop(bid=float(bids[0][0]), ask=float(asks[0][0]))

    async def funding_rate(self, symbol: str) -> float:
        try:
            d = await self._get(self.p.rest_paths["tickers"], category="Futures", symbol=symbol)
            rows = self._rows(d)
            row = rows[0] if isinstance(rows, list) else rows
            return float(row.get("fundingRate", 0) or 0)
        except Exception as e:  # noqa: BLE001
            log.debug("funding fetch failed: %s", e)
            return 0.0

    async def open_orders(self, symbol: str) -> list[Order]:
        d = await self._get(self.p.rest_paths["open_orders"].format(addr=self.main),
                            category="Futures", symbol=symbol, status="open")
        out = []
        for o in self._rows(d) or []:
            cid = str(o.get("clientOrderId", o.get("orderLinkId", o.get("orderId"))))
            side = Side.BUY if str(o.get("side", "")).lower().startswith("b") else Side.SELL
            typ = OrderType.MARKET if "market" in str(o.get("orderType", "")).lower() else OrderType.LIMIT
            created = float(o.get("createdTime", o.get("createdAt", time.time() * 1000))) / 1000
            local = self._local_orders.get(cid)
            out.append(Order(cid, symbol, side, typ, float(o.get("price", 0)), float(o.get("qty", o.get("size", 0))),
                             filled=float(o.get("cumExecQty", o.get("filled", 0)) or 0),
                             created_at=local.created_at if local else created))
        return out

    async def position(self, symbol: str) -> Position:
        d = await self._get(self.p.rest_paths["positions"].format(addr=self.main), category="Futures", symbol=symbol)
        rows = self._rows(d) or []
        row = next((r for r in rows if str(r.get("symbol", "")).upper() == symbol.upper()), None) if isinstance(rows, list) else rows
        if not row:
            return Position(symbol)
        size = float(row.get("size", row.get("qty", 0)) or 0)
        if str(row.get("side", "")).lower().startswith("s"):
            size = -abs(size)
        return Position(symbol, size=size, entry_price=float(row.get("entryPrice", row.get("avgPrice", 0)) or 0),
                        realized_pnl=float(row.get("realisedPnl", row.get("realizedPnl", 0)) or 0))

    async def equity(self) -> float:
        d = await self._get(self.p.rest_paths["balance"].format(addr=self.main))
        data = d.get("data", d)
        for k in ("equity", "totalEquity", "accountValue", "balance"):
            if k in data:
                return float(data[k])
        raise RuntimeError(f"cannot find equity in balance response: {list(data)[:10]}")

    async def poll_fills(self, symbol: str) -> list[Fill]:
        out = []
        while not self._fills.empty():
            f = self._fills.get_nowait()
            if f.symbol.upper() == symbol.upper():
                out.append(f)
        return out

    # ---- WebSocket (fills) -----------------------------------------------
    async def _ws_loop(self) -> None:
        import websockets
        backoff = 2.0
        while True:
            try:
                async with websockets.connect(self.ws_url, ping_interval=None) as ws:
                    await ws.send(json.dumps({"op": "subscribe", "args": [
                        {"walletId": self.main, "topic": "fill"},
                    ]}))
                    backoff = 2.0
                    last_ping = time.time()
                    while True:
                        if time.time() - last_ping > 30:
                            await ws.send("ping")          # plain string, not JSON
                            last_ping = time.time()
                        try:
                            raw = await asyncio.wait_for(ws.recv(), timeout=5)
                        except asyncio.TimeoutError:
                            continue
                        if raw == "pong":
                            continue
                        self._on_ws_message(raw)
            except asyncio.CancelledError:
                return
            except Exception as e:  # noqa: BLE001
                log.warning("ws error: %s; reconnecting in %.0fs", e, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)   # stay well under 30 new connections/min

    def _on_ws_message(self, raw: str) -> None:
        try:
            m = json.loads(raw)
        except json.JSONDecodeError:
            return
        if m.get("topic") != "fill":
            return
        rows = m.get("data", [])
        for f in rows if isinstance(rows, list) else [rows]:
            try:
                side = Side.BUY if str(f.get("side", "")).lower().startswith("b") else Side.SELL
                fee = float(f.get("fee", f.get("execFee", 0)) or 0)
                is_maker = bool(f.get("isMaker", str(f.get("liquidity", "")).lower() == "maker"))
                self._fills.put_nowait(Fill(
                    str(f.get("clientOrderId", f.get("orderId"))), str(f.get("symbol", self.symbol)),
                    side, float(f.get("price", f.get("execPrice"))), float(f.get("qty", f.get("execQty"))),
                    fee, is_maker, float(f.get("ts", f.get("execTime", time.time() * 1000))) / 1000))
            except Exception as e:  # noqa: BLE001
                log.warning("unparsed fill %s: %s", f, e)

    # ---- trading (on-chain) ----------------------------------------------
    def _scale(self, v: float, decimals: int) -> int:
        return int(round(v * 10 ** decimals))

    async def _send_tx(self, data: bytes | str) -> str:
        if isinstance(data, (bytes, bytearray)):
            data = Web3.to_hex(data)
        async with self._tx_lock:
            tx = {"to": ORDER_PRECOMPILE, "data": data, "value": 0, "gas": self.p.gas_limit,
                  "gasPrice": 0, "nonce": self._nonce.next(), "chainId": self.chain_id}
            signed = self.agent.sign_transaction(tx)
            loop = asyncio.get_running_loop()
            h = await loop.run_in_executor(None, self.w3.eth.send_raw_transaction, signed.raw_transaction)
            return h.hex()

    async def place_order(self, symbol, side, type, size, price=None, post_only=True, reduce_only=False) -> Order:
        if self.symbol_id is None:
            raise RuntimeError("symbol_id unresolved")
        is_market = type is OrderType.MARKET
        params = pack_order_params(
            category=2,
            order_type=self.p.enum_market if is_market else self.p.enum_limit,
            side=self.p.enum_buy if side is Side.BUY else self.p.enum_sell,
            tif=self.p.enum_ioc if is_market else (self.p.enum_post_only if post_only else self.p.enum_gtc),
            reduce_only=reduce_only,
        )
        cid = client_order_id()
        cid_str = cid.rstrip(b"\0").decode()
        data = self.order_contract.encode_abi("placeOrder", args=[
            self.main, cid, self.symbol_id, params,
            0 if is_market else self._scale(price, self.p.price_decimals),
            self._scale(size, self.p.qty_decimals),
            0, ZERO_ADDRESS, 0,
        ])
        order = Order(cid_str, symbol, side, type, price, size, post_only=post_only)
        try:
            txh = await self._send_tx(data)
            log.debug("placeOrder tx %s cid=%s", txh, cid_str)
        except Exception as e:  # noqa: BLE001
            msg = str(e).lower()
            if "post" in msg and "only" in msg:
                order.status = "rejected"
                return order
            raise
        if is_market:
            order.status = "filled"
        self._local_orders[cid_str] = order
        return order

    async def cancel_order(self, order_id: str) -> None:
        cid = order_id.encode().ljust(32, b"\0")
        args = Web3().codec.encode(["address", "uint16", "bytes32"], [self.main, self.symbol_id, cid])
        await self._send_tx(self.cancel_selector + args)
        self._local_orders.pop(order_id, None)

    async def cancel_all(self, symbol: str) -> None:
        for o in await self.open_orders(symbol):
            try:
                await self.cancel_order(o.id)
            except Exception as e:  # noqa: BLE001
                log.warning("cancel %s failed: %s", o.id, e)
