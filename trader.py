#!/usr/bin/env python3
"""
Midas Polymarket Trading Bot
Deployed on Render.com (non-US region)
Receives trade commands via HTTP API, executes on Polymarket CLOB
"""

import os
import hmac
import hashlib
import time
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Polymarket CLOB credentials
KEY_ID = os.environ.get("POLY_KEY_ID", "0be336d1-c527-45e4-9b60-eab8ad430082")
SECRET = os.environ.get("POLY_SECRET", "FmD8SxPaoJ+CGVBcqcifGOjdcGW19HNxjv/Rd5D1sE7CbaYBS/VcxYozARkvqI0vxO9wyJktzYRuGB34Pj+vbA==")
POLY_BASE = "https://clob.polymarket.com"

# Risk controls
MAX_TRADE_SIZE_CENTS = int(os.environ.get("MAX_TRADE_CENTS", 500))  # $5 max per trade default
BANKROLL = float(os.environ.get("BANKROLL", 100.0))  # assume $100 bankroll


def signed_headers(method, path, body=""):
    """Build L2 HMAC auth headers for Polymarket CLOB."""
    ts = str(int(time.time()))
    sign_str = ts + method + path + (body or "")
    sig = hmac.new(SECRET.encode(), sign_str.encode(), hashlib.sha256).hexdigest()
    return {
        "POLY_KEY_ID": KEY_ID,
        "POLY_SIGNATURE": sig,
        "POLY_TIMESTAMP": ts,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def poly_get(path):
    r = requests.get(POLY_BASE + path, headers=signed_headers("GET", path))
    return r


def poly_post(path, data):
    r = requests.post(POLY_BASE + path, headers=signed_headers("POST", path, json.dumps(data) if data else ""), json=data)
    return r


def get_markets(limit=50, closed=False):
    """Fetch active markets."""
    r = poly_get(f"/markets?limit={limit}&closed={closed}")
    if r.status_code == 200:
        return r.json().get("data", [])
    return []


def get_live_markets():
    """Get currently active, non-archived markets with volume."""
    r = poly_get("/markets?limit=500&closed=false&archived=false")
    if r.status_code != 200:
        return []
    all_markets = r.json().get("data", [])
    return [m for m in all_markets if m.get("active") and not m.get("archived") and not m.get("closed")]


def size_position(yes_price, edge_pct=0.10):
    """Kelly Criterion Lite: edge / odds × bankroll × 0.3"""
    if yes_price < 0.01:
        return 0
    odds = 1 - yes_price  # implied no price
    if odds <= 0:
        return 0
    edge = edge_pct
    size = (edge / odds) * BANKROLL * 0.3
    size_cents = int(size * 100)
    # Cap at max per trade
    return min(size_cents, MAX_TRADE_SIZE_CENTS)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "midas-trader", "time": time.time()})


@app.route("/trade", methods=["POST"])
def trade():
    """Execute a trade. POST /trade with {condition_id, side, yes_price}"""
    data = request.json or {}
    condition_id = data.get("condition_id")
    side = data.get("side", "BUY").upper()
    yes_price = float(data.get("yes_price", 0))
    size = int(data.get("size_cents", MAX_TRADE_SIZE_CENTS))

    if not condition_id:
        return jsonify({"error": "condition_id required"}), 400
    if size <= 0 or size > MAX_TRADE_SIZE_CENTS:
        return jsonify({"error": f"size_cents must be 1-{MAX_TRADE_SIZE_CENTS}"}), 400

    # Build the order
    order_data = {
        "condition_id": condition_id,
        "size": size / 100.0,  # convert cents to dollars
        "side": side,
        "price": yes_price,
    }

    r = poly_post("/orders", order_data)
    result = {"status": r.status_code, "response": r.text[:200], "order": order_data}

    if r.status_code == 200 or r.status_code == 201:
        return jsonify({"success": True, **result})
    else:
        return jsonify({"success": False, **result}), r.status_code


@app.route("/markets")
def markets():
    """List available markets."""
    live = get_live_markets()
    return jsonify({
        "count": len(live),
        "markets": [
            {
                "condition_id": m.get("condition_id"),
                "question": m.get("question", "")[:80],
                "yes_price": m.get("tokens", [{}])[1].get("price") if len(m.get("tokens", [])) > 1 else None,
                "volume": m.get("volume"),
                "close_time": m.get("end_date_iso"),
            }
            for m in live[:30]
        ]
    })


@app.route("/best-trade")
def best_trade():
    """Find best current trade opportunity based on market scan."""
    live = get_live_markets()
    opportunities = []

    for m in live:
        toks = m.get("tokens", [])
        if len(toks) < 2:
            continue
        yes_tok = toks[1]
        price = yes_tok.get("price", 0)
        volume = float(m.get("volume", 0) or 0)
        if volume < 100 or price <= 0:
            continue

        sz = size_position(price)
        if sz < 50:  # min $0.50
            continue

        opportunities.append({
            "condition_id": m.get("condition_id"),
            "question": m.get("question", "")[:80],
            "yes_price": price,
            "size_cents": sz,
            "volume": volume,
        })

    # Sort by implied edge (price < 0.5 = potential value)
    opportunities.sort(key=lambda x: abs(0.5 - x["yes_price"]), reverse=True)
    return jsonify({"opportunities": opportunities[:5]})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
