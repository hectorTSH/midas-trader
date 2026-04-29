#!/usr/bin/env python3
"""
Midas Polymarket Trading Bot
Deployed on Render.com (non-US region — Frankfurt)
Receives trade commands via HTTP API, executes on Polymarket CLOB
Live market data from SimpleFunctions.dev, trading via CLOB API
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
SF_BASE = "https://simplefunctions.dev/api"

# Risk controls
MAX_TRADE_SIZE_CENTS = int(os.environ.get("MAX_TRADE_CENTS", 500))
BANKROLL = float(os.environ.get("BANKROLL", 100.0))


def signed_headers(method, path, body=""):
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
    return requests.get(POLY_BASE + path, headers=signed_headers("GET", path))


def poly_post(path, data):
    body = json.dumps(data) if data else ""
    return requests.post(POLY_BASE + path, headers=signed_headers("POST", path, body), json=data)


def get_sf_answer(topic):
    """Get probability for a topic from SimpleFunctions."""
    r = requests.get(f"{SF_BASE}/public/answer/{topic}", timeout=10)
    if r.status_code == 200:
        return r.json()
    return None


def scan_sf_markets(query, limit=20):
    """Scan markets on SimpleFunctions."""
    r = requests.get(f"{SF_BASE}/public/scan", params={"q": query, "limit": limit}, timeout=10)
    if r.status_code == 200:
        return r.json()
    return []


def get_live_markets_via_sf():
    """Get live Polymarket markets via SimpleFunctions scan."""
    try:
        r = requests.get(f"{SF_BASE}/public/scan", params={"q": "*", "limit": 50, "venue": "polymarket"}, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        return {"error": str(e)}
    return {"error": "failed"}


def size_position(yes_price, edge_pct=0.10):
    if yes_price < 0.01:
        return 0
    odds = 1 - yes_price
    if odds <= 0:
        return 0
    edge = edge_pct
    size = (edge / odds) * BANKROLL * 0.3
    size_cents = int(size * 100)
    return min(size_cents, MAX_TRADE_SIZE_CENTS)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "midas-trader", "time": time.time()})


@app.route("/trade", methods=["POST"])
def trade():
    """Execute a trade.
    POST /trade with JSON: {condition_id, side, yes_price, size_cents}
    """
    data = request.json or {}
    condition_id = data.get("condition_id")
    side = data.get("side", "BUY").upper()
    yes_price = float(data.get("yes_price", 0))
    size = int(data.get("size_cents", MAX_TRADE_SIZE_CENTS))

    if not condition_id:
        return jsonify({"error": "condition_id required"}), 400
    if size <= 0 or size > MAX_TRADE_SIZE_CENTS:
        return jsonify({"error": f"size_cents must be 1-{MAX_TRADE_SIZE_CENTS}"}), 400
    if yes_price <= 0 or yes_price >= 1:
        return jsonify({"error": "yes_price must be 0-1"}), 400

    order_data = {
        "condition_id": condition_id,
        "size": size / 100.0,
        "side": side,
        "price": yes_price,
    }

    r = poly_post("/orders", order_data)
    result = {"http_status": r.status_code, "response": r.text[:300], "order": order_data}

    if r.status_code in (200, 201):
        return jsonify({"success": True, **result})
    else:
        return jsonify({"success": False, **result}), r.status_code


@app.route("/scan")
def scan():
    """Scan markets by query. ?q=gold&limit=20"""
    q = request.args.get("q", "*")
    limit = int(request.args.get("limit", 20))
    result = scan_sf_markets(q, limit)
    return jsonify(result)


@app.route("/world")
def world():
    """Get world state from SimpleFunctions."""
    r = requests.get(f"{SF_BASE}/agent/world", timeout=15)
    if r.status_code == 200:
        return jsonify(r.json())
    return jsonify({"error": "failed"}), 500


@app.route("/best-trade")
def best_trade():
    """Find best trade opportunities from SimpleFunctions live data."""
    r = requests.get(f"{SF_BASE}/public/scan", params={"q": "*", "limit": 50, "venue": "polymarket", "vol24h_min": 1000}, timeout=15)
    if r.status_code != 200:
        return jsonify({"error": "sf scan failed"}), 500

    markets = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    opportunities = []

    for m in markets:
        price = m.get("price", 0) / 100.0  # price in cents → decimal
        volume = float(m.get("volume24h", 0) or m.get("volume", 0) or 0)
        if volume < 500 or price <= 0:
            continue
        sz = size_position(price)
        if sz < 50:
            continue
        ticker = m.get("bareTicker", m.get("ticker", ""))
        opportunities.append({
            "ticker": ticker,
            "question": m.get("title", "")[:80],
            "yes_price": price,
            "size_cents": sz,
            "volume_24h": volume,
            "spread": m.get("spread", 0),
        })

    opportunities.sort(key=lambda x: x["volume_24h"], reverse=True)
    return jsonify({"opportunities": opportunities[:10]})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
