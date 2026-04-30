---
name: market-scanner
description: Systematically scan Kalshi for high-conviction trading opportunities. Use when: (1) weekly opportunity scan, (2) looking for new trades, (3) checking upcoming events, (4) building watchlist. Trigger phrases: "scan markets", "find opportunities", "watchlist", "upcoming events", "check economic calendar".
---

# Market Scanner

Weekly systematic scan for high-edge trading opportunities on Kalshi.

## Scan Frequency

**Weekly:** Every Monday morning (or after major data releases)
**Event-driven:** Check before CPI, GDP, NFP, Fed announcements

## Scan Workflow

### Step 1: Get All Active Events

```python
def get_all_events():
    resp = requests.get(BASE_URL + "/events?limit=50",
        headers=kalshi_auth("GET", "/events?limit=50"), timeout=10)
    events = resp.json().get("events", [])
    # Group by category
    by_cat = {}
    for e in events:
        cat = e.get("category", "Unknown")
        if cat not in by_cat: by_cat[cat] = []
        by_cat[cat].append(e)
    return by_cat
```

**Priority categories (in order):**
1. **Economics** — GDP, CPI, NFP, Fed decisions (most reliable data, verifiable resolution)
2. **Elections** — High volume, long duration, can have edges far from event
3. **Politics** — Leadership changes, policy outcomes
4. **Crypto** — BTC, ETH price prediction (short-term)

### Step 2: Find Events Closing Within 7 Days

```python
from datetime import datetime, timedelta

def near_term_events(events, days=7):
    cutoff = datetime.now() + timedelta(days=days)
    near = []
    for e in events:
        close = e.get("close_date", e.get("close_time", ""))
        if close:
            try:
                dt = datetime.fromisoformat(close.replace("Z", "+00:00"))
                if dt < cutoff:
                    near.append((dt, e))
            except:
                pass
    return sorted(near)
```

### Step 3: For Each Near-Term Event — Get Markets

```python
def get_event_opportunities(event_ticker, gdnow=None):
    markets = get_markets_by_event(event_ticker)
    opp_list = []
    
    for m in markets:
        bid = float(m.get("yes_bid_dollars", 0))
        ask = float(m.get("yes_ask_dollars", 0))
        last = float(m.get("last_price_dollars", 0))
        mkt_mid = (bid + ask) / 2 if ask > bid else last
        
        # For economic data: compare to GDPNow / base rates
        # For others: compare to historical base rates
        # Calculate edge
        
        vol = float(m.get("volume_24h_fp", 0))
        if vol < 1000:
            continue  # skip illiquid markets
        
        opp_list.append({
            "ticker": m.get("ticker"),
            "q": m.get("title", "")[:60],
            "mkt_price": mkt_mid,
            "vol_24h": vol,
            "close": m.get("close_time", "")[:10]
        })
    
    return sorted(opp_list, key=lambda x: x["vol_24h"], reverse=True)
```

### Step 4: Score Opportunities

**Scoring criteria:**

| Factor | Weight | Notes |
|---|---|---|
| Edge (pp) | 40% | Market vs our probability estimate |
| Volume ($) | 20% | Higher = more liquid |
| Days to close | 15% | Fewer = less uncertainty |
| Resolution clarity | 25% | Can we verify outcome from official data? |

**Threshold for action:** Score > 60 AND edge > 15pp

### Step 5: Build Watchlist

```
Watchlist format:
- Ticker: [event] | Price: $X.XX | Edge: Xpp | Close: MMM-DD | Vol: $XXk
- Notes: why it's interesting, what we're watching for
```

## Economic Event Calendar (US)

| Event | Source | Schedule |
|---|---|---|
| GDP (advance/second/final) | BEA (bea.gov) | Jan/Apr/Jul/Oct, ~8:30 AM ET |
| CPI | BLS (bls.gov/cpi) | ~12-14 days after month, 8:30 AM ET |
| NFP (jobs) | BLS | First Friday of month, 8:30 AM ET |
| Fed rate decision | Fed | 8x/year, 2:00 PM ET |
| PCE inflation | BEA | Monthly, ~8:30 AM ET |
| Retail sales | Census | ~12 days after month, 8:30 AM ET |

## Output Format

After every scan, produce:

```
=== MARKET SCAN: [DATE] ===

HIGH PRIORITY (edge >25pp, vol >$10k):
1. [TICKER] | $X.XX | +XXpp SELL NO | Vol: $XXk | Close: MMM-DD
2. ...

MEDIUM PRIORITY (edge 15-25pp, vol >$5k):
...

WATCHLIST (edge uncertain, high vol):
1. [TICKER] | $X.XX | Vol: $XXk | Close: MMM-DD

ACTION NEEDED:
- [ ] Follow up on [X] before close date
- [ ] Gather [specific data] before resolution
```