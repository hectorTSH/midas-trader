---
name: kalshi-trader
description: Execute live trades on Kalshi prediction markets. Use when: (1) placing, modifying, or canceling orders, (2) checking balance or positions, (3) getting market data, (4) any Kalshi trading action. Trigger phrases: "execute trade", "place order", "check kalshi", "buy on kalshi", "sell no on kalshi", "check balance", "check positions".
---

# Kalshi Trader

Live trading execution for Kalshi prediction markets. All trades are real money.

## Auth Setup (already configured)

```python
KEY_ID = "fdbce304-fcd3-4be8-a735-1c6825e932c7"
KEY_PATH = "/Users/hamallar/.kalshi/key.pem"
BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
```

## Core Functions

```python
import base64, time, requests
from urllib.parse import urlparse
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

def kalshi_auth(method, path):
    ts = str(int(time.time() * 1000))
    sign_path = urlparse(BASE_URL + path).path  # must be the URL path from root
    msg = f"{ts}{method}{sign_path}".encode()
    sig = base64.b64encode(pk.sign(msg, padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.DIGEST_LENGTH
    ), hashes.SHA256())).decode()
    return {
        "KALSHI-ACCESS-KEY": KEY_ID,
        "KALSHI-ACCESS-TIMESTAMP": ts,
        "KALSHI-ACCESS-SIGNATURE": sig,
        "Content-Type": "application/json"
    }
```

## Trade Execution

**SELL NO (our primary trade type):**
```python
def sell_no(ticker, count, price_str):
    payload = {
        "ticker": ticker,
        "side": "no",
        "count": count,
        "no_price_dollars": price_str,  # STRING, not float
        "action": "buy"  # always "buy" action
    }
    resp = requests.post(BASE_URL + "/portfolio/orders",
        json=payload, headers=kalshi_auth("POST", "/portfolio/orders"), timeout=10)
    return resp.status_code == 201, resp.json()
```

**BUY YES:**
```python
def buy_yes(ticker, count, price_str):
    payload = {
        "ticker": ticker,
        "side": "yes",
        "count": count,
        "yes_price_dollars": price_str,  # STRING
        "action": "buy"
    }
    resp = requests.post(BASE_URL + "/portfolio/orders",
        json=payload, headers=kalshi_auth("POST", "/portfolio/orders"), timeout=10)
    return resp.status_code == 201, resp.json()
```

## Balance & Positions

```python
def get_balance():
    resp = requests.get(BASE_URL + "/portfolio/balance",
        headers=kalshi_auth("GET", "/portfolio/balance"), timeout=10)
    d = resp.json()
    return d.get("balance", 0) / 100, d.get("portfolio_value", 0) / 100

def get_positions():
    resp = requests.get(BASE_URL + "/portfolio/positions",
        headers=kalshi_auth("GET", "/portfolio/positions"), timeout=10)
    return resp.json()
```

## Market Data

```python
def get_market(ticker):
    resp = requests.get(BASE_URL + f"/markets/{ticker}",
        headers=kalshi_auth("GET", f"/markets/{ticker}"), timeout=10)
    return resp.json().get("market", {}) if resp.status_code == 200 else None

def get_events(category=None):
    path = "/events?limit=50"
    if category: path += f"&category={category}"
    resp = requests.get(BASE_URL + path,
        headers=kalshi_auth("GET", path), timeout=10)
    return resp.json().get("events", []) if resp.status_code == 200 else []

def get_markets_by_event(event_ticker):
    resp = requests.get(BASE_URL + f"/markets?event_ticker={event_ticker}",
        headers=kalshi_auth("GET", f"/markets?event_ticker={event_ticker}"), timeout=10)
    return resp.json().get("markets", []) if resp.status_code == 200 else []
```

## Workflow for Each Trade

1. **Check balance** → `get_balance()`
2. **Confirm price** → `get_market(ticker)` — read yes_bid/yes_ask
3. **Calculate position cost** → `count × price`
4. **Verify <10% bankroll** → `cost / balance < 0.10`
5. **Execute** → `sell_no()` or `buy_yes()`
6. **Confirm** → check response status 201, print fill summary

## Key Rules
- Price must be STRING: `"0.53"` not `0.53`
- Use `count` (integer), not `shares`
- Use `side: "no"` for sell NO, `side: "yes"` for buy YES
- All prices in dollars (not cents)
- Sleep 1s between API calls to avoid rate limits

## Gotchas
- Order fills IMMEDIATELY at market price — no resting orders
- Fee is charged on fill: ~2% of notional
- Balance updates after fill — read new balance before sizing next trade
