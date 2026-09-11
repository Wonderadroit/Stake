# STAKE — PROJECT BIBLE

## 1. Mission

STAKE is a **sports-betting market-behavior research engine**.

Its purpose is to investigate whether observable betting-market behavior contains reproducible evidence of:

- information flow,
- price discovery,
- informed trading,
- temporary mispricing,
- market inefficiency,
- or other statistically defensible structure.

STAKE is **not** defined as a betting bot, a guaranteed-profit system, or a "smart money detector." It must not assume that an odds movement was caused by smart money merely because the movement was large or profitable after the fact.

The central research principle is:

> **Observe market behavior → form a falsifiable hypothesis → test it historically → compare against controls → keep only what survives.**

---

## 2. Research Doctrine

STAKE must understand market behavior before attempting to exploit it.

The project prioritizes:

1. Temporal ordering.
2. Cross-bookmaker behavior.
3. Market convergence and divergence.
4. Persistence versus reversal.
5. Closing-line behavior.
6. CLV (Closing Line Value).
7. Out-of-sample performance.
8. Proper controls and baselines.
9. Reproducibility.
10. Falsification over confirmation.

STAKE must preserve uncertainty. A detected movement is an observation, not an explanation.

### Forbidden shortcut

```text
odds moved → smart money
```

### Preferred reasoning

```text
bookmaker quotes
    ↓
odds movement
    ↓
temporal order
    ↓
leader/follower structure
    ↓
cross-book convergence
    ↓
persistence or reversal
    ↓
closing-line movement
    ↓
CLV
    ↓
ROI / statistical evaluation
```

---

## 3. Current Core Hypothesis

The current research direction is whether **leader → follower information propagation** contains predictive information about later market consensus and closing-line movement.

A candidate sequence is:

```text
Book A moves
      ↓
Book B/C/D follow
      ↓
market converges
      ↓
new consensus persists
      ↓
closing line confirms or rejects direction
      ↓
measure CLV
      ↓
measure ROI
```

The research question is not:

> "Can we identify smart money?"

It is:

> **Does the temporal structure of bookmaker repricing contain information that predicts subsequent market behavior better than appropriate controls?**

Possible interpretation labels should therefore use cautious language such as:

- `PRICE_DISCOVERY_CANDIDATE`
- `INFORMED_MONEY_CANDIDATE`
- `LEADER_FOLLOWER_EVENT`
- `PERSISTENT_CONVERGENCE`
- `REVERSAL_EVENT`
- `ISOLATED_BOOK_EVENT`

These labels are hypotheses or classifications, not proof of cause.

---

## 4. Market Analogy

Financial-market concepts can be useful research analogies, but they must not be treated as proof that betting markets work identically to financial markets.

| Market research concept | Betting-market analogue |
|---|---|
| Asset price | Betting line / quoted price |
| Buy pressure | Money backing one side |
| Sell pressure | Money backing the other side |
| Price discovery | Odds moving toward a new consensus |
| Informed trader | Potential informed bettor/trading participant |
| Order-book propagation | Cross-bookmaker repricing |
| Momentum | Persistent directional repricing |
| Mean reversion | Reversal after an initial move |
| Market leader | First observable bookmaker to reprice |
| Followers | Books repricing after the leader |

The analogy is a source of hypotheses, **not evidence**.

---

## 5. Event Regimes

STAKE should distinguish at least these regimes:

### A. Leader → Followers
One bookmaker moves first and other books subsequently move in the same direction.

### B. Isolated Bookmaker
One bookmaker moves while the broader market does not follow.

### C. Leader → Reversal
An initial leader movement is followed by reversal or rejection.

### D. Leader → Followers → Persistent Consensus
A leader moves, other books follow, and the new consensus persists toward the close.

Regime D is currently the most important research candidate because it connects observable temporal propagation to closing-line behavior.

---

## 6. Information Propagation

STAKE should measure propagation rather than only direction.

Example:

```text
T+00  Book A moves
T+08  Book B moves
T+15  Book C moves
T+27  Book D moves
T+41  Book E moves
      ↓
new consensus
      ↓
closing line
```

Useful measurements include:

- first-mover identity,
- first-move timestamp,
- follower timestamps,
- follower count,
- propagation speed,
- movement magnitude,
- cross-book dispersion before movement,
- cross-book dispersion after movement,
- convergence speed,
- persistence duration,
- reversal frequency,
- closing-line displacement,
- CLV,
- ROI.

Simultaneous movement, random movement, and isolated movement are important controls.

---

## 7. Current STAKE Architecture

The intended research pipeline is:

```text
RAW DATA
   ↓
NORMALIZATION
   ↓
MARKET OBSERVATION
   ↓
LOCAL MOVEMENT
   ↓
EVENT CLASSIFICATION
   ↓
LEADER / FOLLOWER
   ↓
CONVERGENCE
   ↓
PERSISTENCE
   ↓
CLOSING-LINE EVALUATION
   ↓
CLV
   ↓
OUTCOME / ROI
   ↓
STATISTICAL / FALSIFICATION REPORT
```

The architecture should remain experimental. Do not create layers merely because they look architecturally complete.

A new module is justified only when it answers a defined research question and can be demonstrated against historical data.

---

## 8. AH-04 Research Track

AH-04 is the current timestamped Asian-handicap market research track.

Important existing components include:

- `stake/ah04.py` — strict temporal window construction.
- `stake/ah04_metrics.py` — probability-pressure and displacement primitives.
- `stake/ah04_v5.py` — local movement/event primitives.
- `scripts/run_ah04_v5.py` — V5 historical scanner.
- `scripts/run_ah04_v5_1.py` — current V5.1 historical scanner.
- `tests/test_ah04.py` — temporal-window tests.

### Temporal semantics

The project uses strict event timing:

- **before:** latest tick at or before the information timestamp;
- **after:** earliest tick strictly after the information timestamp and before kickoff;
- **close:** latest tick strictly before kickoff;
- observations at or after kickoff are invalid for pre-kickoff analysis.

These semantics are part of the research integrity and must not be weakened casually.

---

## 9. Current V5 / V5.1 State

The V5 work extracts local market-event primitives from timestamped bookmaker data.

Current event concepts include:

- `INSUFFICIENT_COVERAGE`
- `VERY_STRONG_LOCAL_PRESSURE`
- `PRESSURE_BEFORE_LINE_REVERSAL`
- `PRESSURE_BEFORE_LINE`
- `LINE_BEFORE_PRESSURE`
- `LOCAL_PRESSURE_ONLY`
- `LINE_ONLY`
- `NO_STRONG_EVENT`

V5.1 was specifically adjusted so that local events are not dependent on T-180 baseline coverage. This is important: lack of a long baseline must not automatically erase a valid local event.

The current pressure threshold is `0.015`, with strong/very-strong bookmaker counts used by the scanner. **Do not lower thresholds simply to manufacture more events.** If event yield is low, investigate whether the phenomenon is genuinely rare, whether the measurement is wrong, or whether the research question needs to change.

---

## 10. Data

The public/sample dataset used by the current AH-04 work is the European Football Asian Handicap Odds Time-Series dataset.

The repository expects the local raw sample at:

```text
data/raw/ah04/sample/sample/EPL/2024-2025
```

Raw data is intentionally gitignored. The code repository should contain the experiment logic and reproducible instructions without pretending that local raw data is present in GitHub.

The described dataset contains timestamped bookmaker observations across major European leagues and multiple bookmakers, making it suitable for temporal market-structure research.

Do not hard-code conclusions from the sample. A result from a small public sample is a research observation that must eventually be tested on broader data.

---

## 11. Data and Formula Integrity

Do not silently change odds interpretation or probability formulas.

`stake/ah04_metrics.py` currently uses normalized two-way probabilities derived from the dataset's Asian-style payout-price convention. Before changing this, inspect actual raw observations and establish the dataset's odds convention.

Any formula change must include:

1. a documented reason;
2. representative raw examples;
3. tests;
4. before/after impact on historical results;
5. a clear decision about whether old results remain comparable.

---

## 12. Falsification Rules

STAKE must actively try to kill its hypotheses.

A candidate signal is weak if it disappears when:

- bookmaker identity is randomized;
- event timestamps are shuffled within valid windows;
- direction is randomized;
- simultaneous moves are treated as leaders;
- isolated movements are included as if they were propagation events;
- a simple consensus baseline performs equally well;
- a random-bookmaker control performs equally well;
- the effect disappears out of sample;
- the effect disappears after reasonable transaction/margin assumptions;
- the effect is explained by leakage from closing information.

The project must report negative results rather than hiding them.

---

## 13. Leakage Rules

No signal may use information that would not have been available at the moment the signal is declared.

Especially forbidden:

- using the closing line to define an event that is then claimed to predict the closing line;
- using match outcome to classify a pre-match signal;
- using future bookmaker movements to decide which bookmaker was the leader;
- selecting thresholds after seeing only favorable test results without a held-out evaluation.

The close is an **evaluation target**, not a hidden input to the signal.

---

## 14. Controls

Every meaningful leader/follower experiment should consider controls such as:

1. Random bookmaker selected as leader.
2. Consensus movement without leader identification.
3. Randomized leader timestamps.
4. Simultaneous-movement control.
5. Isolated-book control.
6. Baseline market movement without event classification.
7. Out-of-sample temporal validation.

The strongest result is not "our event won." It is:

> **Our event explains or predicts later market behavior better than credible alternative explanations.**

---

## 15. CLV and ROI

STAKE should separate three questions:

### Market prediction
Did the event predict subsequent market movement?

### Price quality
Did the event obtain a better price than the eventual closing market?

### Economic value
Did the resulting strategy survive actual settlement assumptions and produce positive out-of-sample ROI?

A positive CLV result is not automatically proof of positive ROI.

A positive ROI on a small sample is not automatically proof of a durable edge.

---

## 16. Experimental Discipline

The project follows this loop:

```text
QUESTION
  ↓
MINIMAL IMPLEMENTATION
  ↓
HISTORICAL TEST
  ↓
CONTROL
  ↓
RESULT
  ↓
FALSIFY / REFINE / ACCEPT PROVISIONALLY
  ↓
DOCUMENT
```

Do not build a large architecture ahead of evidence.

Do not optimize for impressive event counts.

Do not optimize thresholds against the same historical sample used for final evaluation.

Do not confuse a plausible story with an empirical result.

---

## 17. Current Research Checkpoint — 2026-09-11

### Repository

`Wonderadroit/Stake`

### Latest known main commit

`d40b2058e94310712ddd59c349042c7e4a46e5ea`

Commit message:

`fix: make AH-04 V5 local events independent of T-180 coverage`

Recent preceding work:

- `ab824e6a41352e6757b237e71516e7081a26a467` — extract AH-04 V5 local event primitives.
- `7a5363cbe9893341025b135e35f2c550bfae7948` — add AH-04 V5 local movement event sequence scanner.

### Current state

AH-04 V5/V5.1 local event detection exists and has been tested in the repository. The next research layer is **not** to loosen thresholds or generate more events. The next layer is to determine whether observable local movements contain a meaningful leader/follower and price-discovery structure.

### Immediate next action

Before creating a V6 leader/follower implementation:

1. Pull latest `main` locally.
2. Run the complete test suite.
3. Run `scripts/run_ah04_v5_1.py`.
4. Inspect `data/ah04_v5_1_scan.csv`.
5. Count event classes.
6. Inspect representative events and their timestamps/books.
7. Confirm what the local data actually supports.
8. Only then design the smallest next experiment.

### Required local commands

```bash
cd ~/Stake
git pull origin main
pytest -q
PYTHONPATH=. python scripts/run_ah04_v5_1.py
ls -lh data/ah04_v5_1_scan.csv
```

Then inspect the resulting event classes and representative rows.

### Current hypothesis

```text
leader
  ↓
followers
  ↓
market convergence
  ↓
persistent new consensus
  ↓
closing-line movement
  ↓
CLV
  ↓
ROI
```

### Current prohibition

Do **not** describe an odds movement as "smart money" merely because it was followed by a favorable outcome.

Do **not** add a leader/follower module until the V5.1 output has been inspected and the exact measurable event definition is clear.

---

## 18. Long-Term Direction

If the current hypothesis survives testing, STAKE can evolve toward a general market-event research engine capable of studying:

- Asian handicap;
- totals;
- moneyline / 1X2;
- cross-market propagation;
- bookmaker leadership;
- line movement;
- market disagreement;
- information arrival;
- persistence and reversal;
- CLV;
- out-of-sample economic evaluation.

The long-term goal is **not** to build a machine that blindly predicts winners.

The long-term goal is to understand market behavior well enough to identify statistically reproducible structures and know exactly where they fail.

---

## 19. Definition of Success

STAKE succeeds when it can make claims of this form:

> "Under these exact observable conditions, using only information available at event time, the market subsequently behaved differently from the specified controls, with the effect surviving out-of-sample validation."

STAKE fails when it makes claims of this form:

> "The odds moved, therefore smart money knew the result."

The first is research.

The second is storytelling.

**STAKE is committed to the first.**
