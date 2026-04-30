---
name: gdp-edge
description: Detect mispricing in Kalshi GDP prediction markets using the Atlanta Fed GDPNow nowcast as the primary edge signal. Use when: (1) scanning for GDP trade opportunities, (2) before any GDP release, (3) analyzing KXGDP market buckets, (4) deciding whether to buy YES or sell NO on GDP thresholds. Trigger phrases: "gdp trade", "gdpnow", "gdp analysis", "scan gdp", "economic data trade".
---

# GDP Edge Detection

Find and size GDP prediction market trades using the Atlanta Fed GDPNow model as the primary data source.

## Primary Signal: GDPNow

**URL:** https://fred.stlouisfed.org/series/GDPNOW/
**Update:** Continuously as economic data comes in
**Frequency check:** Before every GDP release + weekly scan

The GDPNow model aggregates ~60 economic indicators into a single real-time growth estimate. It's the best publicly available nowcast for Q1/Q2/Q3/Q4 GDP.

## Core Analysis

```python
import math

def norm_cdf(z):
    """Standard normal CDF approximation."""
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))

def gdp_edge_analysis(gdnow_estimate, thresholds_with_prices):
    """
    gdnow_estimate: float, e.g. 1.2 for 1.2% growth
    thresholds_with_prices: list of (threshold_float, market_mid_float)
    
    Returns edge analysis for each bucket.
    """
    std_error = 0.8  # typical GDPNow std error vs actual
    
    results = []
    for threshold, mkt_price in thresholds_with_prices:
        z = (threshold - gdnow_estimate) / std_error
        calc_prob = 1 - norm_cdf(z)
        edge_pp = mkt_price - calc_prob
        edge_pct = edge_pp * 100
        
        direction = "SELL NO" if mkt_price > calc_prob else "BUY YES"
        if abs(edge_pp) < 0.05:
            direction = "SKIP"
        
        results.append({
            "threshold": threshold,
            "calc_prob": calc_prob,
            "mkt_price": mkt_price,
            "edge_pp": edge_pp,
            "direction": direction,
            "win_prob": 1 - calc_prob if direction == "SELL NO" else calc_prob,
            "payout": (mkt_price / (1 - mkt_price)) if direction == "SELL NO" else ((1 - mkt_price) / mkt_price)
        })
    return results
```

## Decision Rules

**Before placing any GDP trade:**

1. **Get fresh GDPNow estimate** — Search or check FRED (https://fred.stlouisfed.org/series/GDPNOW/)
2. **Build threshold map** — All KXGDP buckets for that event
3. **Calculate edge for each bucket** — `calc_prob vs mkt_price`
4. **Find maximum edge bucket** — Where market most over/under-prices vs GDPNow
5. **Check direction consistency** — GDPNow 1.2% means sell NO on low thresholds (1.0%, 1.5%, 2.0%, 2.5%)
6. **Size position** — Max 10% bankroll per trade
7. **Write EV before executing** — Required for every trade

## Example: 2026-04-29 GDPNow = 1.2%

| Threshold | Calc P | Mkt Price | Edge | Direction |
|---|---|---|---|---|
| >1.0% | 60% | 95% | +35pp | SELL NO |
| >1.5% | 35% | 89% | +54pp | SELL NO |
| >2.0% | 16% | 80% | +64pp | **SELL NO** ← highest edge |
| >2.5% | 5% | 53% | +48pp | SELL NO |
| >3.0% | 1% | 32% | +31pp | SELL NO |

**Best trade:** SELL NO on the threshold closest to GDPNow estimate where market overshoots most.

## GDPNow vs Market Price — Key Principle

The market prices GDP probability based on crowd sentiment + news. GDPNow is mechanical. When they disagree by >20pp, the mechanical model has historically been right on short-term events.

**Historical pattern:**
- Market overprices low thresholds (1.0%, 1.5%, 2.0%) when GDPNow is low
- Market underprices high thresholds (3.0%+) when GDPNow is moderate
- The larger the gap, the higher the edge

## Risk Controls

- **Never bet against GDPNow >3.5%** — it's only happened ~5% of the time historically
- **Minimum 15pp edge** before placing — below that, not enough edge to justify the risk
- **One threshold per event** — avoid cross-canceling positions (GDP 2.3% wins T2.5 YES AND loses T2.0 YES)
- **Scale as bankroll grows** — from 10% at $100 to 5% at $1000

## Data Sources

| Source | URL | Use |
|---|---|---|
| GDPNow FRED | https://fred.stlouisfed.org/series/GDPNOW/ | Primary nowcast |
| BEA GDP Release | https://www.bea.gov/data/gdp | Official release schedule |
| Atlanta Fed Commentary | https://www.atlantafed.org/research-and-data/data/gdpnow/current-and-past-gdpnow-commentaries | Model updates |
| BLS CPI | https://www.bls.gov/cpi | CPI release schedule |
| BLS NFP | https://www.bls.gov/bls/latest-numbers.htm | Jobs data schedule |

## Check Schedule

BEA GDP releases: ~30 days after quarter end (late April for Q1)
BLS CPI: ~12-14 days after month (mid-month)
BLS NFP: First Friday of month
Fed decisions: 8 times/year, scheduled
