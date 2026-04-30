---
name: education-pipeline
description: Continuously collect and process high-signal trading research. Use when: (1) Hector says "research", "find sources", (2) scanning for new strategies, (3) building the knowledge base, (4) heartbeat-triggered research. Trigger phrases: "research trading strategies", "find high signal sources", "education pipeline", "collect research", "scan for strategies".
---

# Education Pipeline

Twice-weekly systematic research collection to continuously improve Midas's trading edge.

## Schedule

- **Every heartbeat cycle** (every ~12h): light scan — check for major market-moving news
- **Every 3-4 days**: full research run — web search + save to inbox
- **After every trade**: record outcome + lessons

## Research Sources (Priority Order)

### Tier 1: Official Data & Primary Sources
- Atlanta Fed GDPNow commentary (fred.stlouisfed.org)
- BLS data releases (bls.gov)
- BEA press releases (bea.gov)
- Fed Reserve publications (federalreserve.gov)
- IMF/World Bank outlooks

### Tier 2: Prediction Market Research
- Metaculus blog / research posts
- Metaculus prediction accuracy track records
- Good Judgment Project findings (Tetlock)
- Polymarket research / announcements
- Kalshi blog / research

### Tier 3: Trading Strategy
- Academic papers on prediction market efficiency
- Practitioner guides (Realistic栩⸣)
- Bot/trading strategy write-ups (Medium, Substack)
- Reddit r/ predictionmarkets, r/algotrading

## Research Workflow

### Step 1: Search for Current High-Signal Content

```bash
# Run these searches in rotation:
web_search --count 5 --freshness month --query "prediction market trading strategies economic data 2026"
web_search --count 5 --freshness month --query "kalshi trading winning strategies 2026"
web_search --count 5 --freshness month --query "GDPNow prediction accuracy analysis"
web_search --count 5 --freshness month --query "Philip Tetlock superforecasting trading application"
web_search --count 5 --freshness month --query "prediction market arbitrage efficiency 2026"
```

### Step 2: Fetch and Assess Quality

For each promising result:
- Open URL, read key sections
- Assess: Is this specific and actionable OR vague and generic?
- Reject: pure opinion, no data, repeating common knowledge
- Keep: specific numbers, backtested results, original research, verifiable claims

### Step 3: Save to Inbox

```bash
# Save format: ~/Vault/00-inbox/YYYY-MM-DD-[source-name]-[topic].md

# Frontmatter:
# Source: [publication/url]
# Date: YYYY-MM
# Signal: HIGH/MEDIUM/LOW
# Notes: key findings, data points, trading implications
```

### Step 4: Process via process-inbox Skill

```bash
# Run process-inbox after every research run
# Files move from 00-inbox/ to 01o-captures/
# System tags: observations, patterns, questions, numbers, reactions
```

### Step 5: Update Connection Notes

After processing, look for patterns across research → update or create new connection files in `~/Vault/02-connections/`

## Quality Bar

**HIGH signal sources must have:**
- Specific numbers or data (not just opinions)
- Named sources or methodology
- Verifiable claims
- Direct trading application

**Reject if:**
- Vague assertions ("prediction markets are efficient")
- No original data
- Generic advice ("always manage risk")
- Promotional content without substance

## Track What Works

After each research run, note in `~/Vault/30-Midas/memory/sessions/`:
- What did we learn?
- Did it suggest a trade?
- Did that trade work? Why/why not?

This compounds into a proprietary insight library over time.