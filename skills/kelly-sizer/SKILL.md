---
name: kelly-sizer
description: Calculate optimal position size for any trade using Kelly Criterion adjusted for real-world constraints. Use when: (1) sizing a trade, (2) checking if a position is within risk limits, (3) calculating expected value, (4) allocating bankroll across multiple trades. Trigger phrases: "size position", "kelly criterion", "position sizing", "check risk limits", "expected value", "allocate bankroll".
---

# Kelly Criterion Position Sizer

Calculate the right trade size for any prediction market opportunity.

## Core Kelly Formula

```python
def kelly_fraction(win_prob, odds):
    """
    win_prob: probability of winning (0 to 1)
    odds: payout ratio = win_amount / loss_amount
    Returns Kelly fraction (0 to 1)
    """
    if odds <= 0:
        return 0
    bp = win_prob * odds - (1 - win_prob)
    return max(bp / odds, 0)  # never return negative Kelly

def kelly_size(bankroll, win_prob, odds, safety=0.3):
    """
    bankroll: total capital available ($)
    win_prob: our estimated probability
    odds: payout ratio
    safety: multiply Kelly by this (0.3 = "fractional Kelly 1/3")
    Returns: dollar amount to risk
    """
    k = kelly_fraction(win_prob, odds)
    return bankroll * k * safety
```

## Quick Reference Tables

**SELL NO sizing (our primary trade type):**

| Market Price | Win Payout | Kelly@60% | Kelly@70% | Kelly@80% |
|---|---|---|---|---|
| $0.79 (21% YES) | 0.27 | 7.2% | 12.5% | 18% |
| $0.53 (47% YES) | 0.89 | 13.3% | 23.2% | 33.2% |
| $0.32 (68% YES) | 2.12 | 13.3% | 23.2% | 33.2% |

**BUY YES sizing:**

| Market Price | Win Payout | Kelly@60% | Kelly@70% | Kelly@80% |
|---|---|---|---|---|
| $0.20 (80% YES) | 4.00 | 10% | 17.5% | 25% |
| $0.50 (50% YES) | 1.00 | 5% | 10% | 15% |
| $0.80 (20% YES) | 0.25 | 0% (negative) | 0% | 2.5% |

## Risk Rules (Non-Negotiable)

```
Max per trade: 10% of bankroll (aggressive mode)
Max per trade: 5% of bankroll (normal mode)
Max total at risk: 25% of bankroll in correlated positions
Daily loss limit: -10% → STOP trading for the day
```

## EV Calculation (Required Before Every Trade)

```python
def expected_value(size, win_prob, payout):
    """
    size: dollar amount at risk
    win_prob: our estimated probability
    payout: multiplier when we win (e.g., 0.47 means win 47% of stake)
    Returns: expected dollar value
    """
    win = size * payout
    loss = size
    ev = win_prob * win - (1 - win_prob) * loss
    return ev

def ev_pct(size, win_prob, payout):
    """EV as percentage of stake."""
    ev = expected_value(size, win_prob, payout)
    return ev / size * 100
```

## Quick EV Calculator

```
Trade: SELL NO 19 shares @ $0.53 on KXGDP T2.5
Cost: $10.07 | Payout: $8.93 if wins | Win prob: 93%

EV = 0.93 × $8.93 - 0.07 × $10.07
EV = $8.30 - $0.70
EV = +$7.60 (+75% ROI on the bet)
```

## Position Check Formula

```python
def check_risk(balance, position_cost, max_pct=0.10):
    """
    Returns (within_limit: bool, risk_pct: float, message: str)
    """
    risk_pct = position_cost / balance
    within_limit = risk_pct <= max_pct
    message = f"Position size: {risk_pct*100:.1f}% of bankroll (max {max_pct*100:.0f}%)"
    return within_limit, risk_pct, message
```

## Sizing Workflow

1. **Input:** bankroll, market price, our probability estimate
2. **Calculate:** `odds = (1 - market_price) / market_price` for SELL NO
3. **Calculate:** `kelly_size = kelly_fraction × bankroll × 0.3`
4. **Cap:** `min(kelly_size, balance × 0.10)` — never exceed 10%
5. **Verify:** `cost ≤ balance × 10%`
6. **Write EV:** `ev = win × p_win - loss × p_loss`
7. **Execute only if:** `EV > 0` and `edge > 15pp`