#!/usr/bin/env python3
"""Create an Agent Key and approve it from the main wallet (Python port of the
ethers script in docs/popdex-api-notes.md).

Usage:
    read -rs MAIN_PRIVATE_KEY && export MAIN_PRIVATE_KEY
    python scripts/approve_agent.py [--testnet]
    unset MAIN_PRIVATE_KEY

Writes agent_key.ini (mode 600) *before* sending the approval, so a crash
mid-flight never leaves an approved agent whose key you don't have.
Never commit agent_key.ini.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from eth_account import Account
from web3 import Web3

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mmbot.exchange.popdex import ACCOUNT_PRECOMPILE, MAINNET, TESTNET  # noqa: E402

ACCOUNT_ABI = [
    {"type": "function", "name": "approveAgent", "stateMutability": "nonpayable", "outputs": [],
     "inputs": [{"name": "agent", "type": "address"}, {"name": "delegator", "type": "address"},
                {"name": "name", "type": "bytes32"}, {"name": "expiresAt", "type": "uint64"},
                {"name": "nonce", "type": "uint64"}]},   # last arg name truncated in source article
    {"type": "function", "name": "getAgents", "stateMutability": "view",
     "inputs": [{"name": "delegator", "type": "address"}],
     "outputs": [{"name": "agents", "type": "address[]"}, {"name": "expires", "type": "uint64[]"}]},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--testnet", action="store_true")
    ap.add_argument("--out", default="agent_key.ini")
    a = ap.parse_args()
    net = TESTNET if a.testnet else MAINNET

    pk = os.environ.get("MAIN_PRIVATE_KEY")
    if not pk:
        sys.exit("MAIN_PRIVATE_KEY is not set")
    if Path(a.out).exists():
        sys.exit(f"{a.out} already exists; move it away first (never reuse an agent address)")

    w3 = Web3(Web3.HTTPProvider(net["rpc_url"], request_kwargs={"timeout": 15}))
    main_acct = Account.from_key(pk)
    acct = w3.eth.contract(address=ACCOUNT_PRECOMPILE, abi=ACCOUNT_ABI)

    try:
        agents, _ = acct.functions.getAgents(main_acct.address).call()
        print(f"current agents: {len(agents)} / 10")
        if len(agents) >= 10:
            sys.exit("agent limit reached; revoke an old one first")
    except Exception as e:  # noqa: BLE001
        print(f"getAgents failed ({e}); account may not exist yet - have you deposited?")

    agent = Account.create()
    print("new agent address:", agent.address)

    def save(approved: bool, txh: str):
        Path(a.out).write_text(
            "[DEFAULT]\n"
            f"agent_address = {agent.address}\n"
            f"agent_private_key = {agent.key.hex()}\n"
            f"main_address = {main_acct.address}\n"
            f"approved = {str(approved).lower()}\n"
            f"approved_tx = {txh}\n"
            f"network = {'testnet' if a.testnet else 'mainnet'}\n")
        os.chmod(a.out, 0o600)

    save(False, "")
    print(f"key saved to {a.out} (before approval)")

    data = acct.encode_abi("approveAgent", args=[
        agent.address, main_acct.address, b"\0" * 32, 0, int(time.time() * 1000)])
    tx = {"to": ACCOUNT_PRECOMPILE, "data": data, "value": 0, "gas": 1_000_000, "gasPrice": 0,
          "nonce": int(time.time() * 1000), "chainId": net["chain_id"]}
    signed = main_acct.sign_transaction(tx)
    txh = w3.eth.send_raw_transaction(signed.raw_transaction)
    print("sent tx:", txh.hex())
    rc = w3.eth.wait_for_transaction_receipt(txh, timeout=60)
    ok = rc["status"] == 1
    print("result:", "success" if ok else "FAILED")
    if ok:
        save(True, txh.hex())
        print(f"done. verify at {net['rest_url']}/api/v1/account/{main_acct.address}/agents")


if __name__ == "__main__":
    main()
