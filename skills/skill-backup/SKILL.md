---
name: skill-backup
description: Automatically back up any newly created or modified trading skills to the Midas GitHub repo. Use when: (1) creating a new skill related to trading, markets, or trading education, (2) significantly modifying an existing trading skill, (3) Hector says "backup my skills" or "push skills to GitHub". Trigger phrases: "backup skills", "push skills to github", "save skills to repo", "sync skills".
---

# Skill Backup

Automatically back up any newly created or modified trading skills to the Midas GitHub repo.

## When This Skill Triggers

- After creating ANY new skill in `~/.openclaw/workspace/skills/` related to trading, markets, prediction markets, or trading education
- After significantly updating an existing skill
- On request: "backup skills", "push skills to GitHub"

## Backup Workflow

### Step 1: Identify Skills to Back Up

```bash
# Find all skill directories in workspace/skills
ls ~/.openclaw/workspace/skills/

# Identify trading-related skills (exclude system skills)
# Trading skills typically have names like:
# kalshi-*, gdp-*, kelly-*, market-*, education-*, trading-*, prediction-*, polymarket-*, arbitrage-*, scanner-*, etc.
```

### Step 2: Copy to GitHub Repo

```bash
# Repo path: ~/midas-trader/
REPO=~/midas-trader
SKILLS_DIR=~/.openclaw/workspace/skills

# Copy each trading skill to the repo's skills/ folder
cp -r $SKILLS_DIR/kalshi-trader $REPO/skills/
cp -r $SKILLS_DIR/gdp-edge $REPO/skills/
cp -r $SKILLS_DIR/kelly-sizer $REPO/skills/
cp -r $SKILLS_DIR/market-scanner $REPO/skills/
cp -r $SKILLS_DIR/education-pipeline $REPO/skills/
# Add any other trading skill as needed
```

### Step 3: Commit and Push

```bash
cd ~/midas-trader
git add -A
git commit -m "Backup trading skills — $(date '+%Y-%m-%d')"
git push
```

## GitHub Repo

**URL:** https://github.com/hectorTSH/midas-trader
**Description:** Autonomous AI trading bot for prediction markets and crypto
**Skills folder:** `skills/` in the repo

## Naming Convention

When adding new skills, use lowercase with hyphens:
- ✅ `kalshi-trader`, `gdp-edge`, `superforecasting`
- ❌ `Kalshi Trader`, `GDP Edge`, `SuperForecasting`

## Trigger Check

Before every skill creation, ask: "Is this related to trading, markets, or trading education?"
If YES → immediately back up after the skill is complete.

## Post-Backup Verification

After pushing, confirm with:
```
✅ Skills backed up to github.com/hectorTSH/midas-trader
   - [skill-name-1]
   - [skill-name-2]
```
