# STAKE — PROJECT BIBLE

## 1. Mission

STAKE is a **sports-market behavior research engine** for authorized historical market research.

Its job is to determine, with reproducible evidence, whether observable price/odds behavior contains information about **future market behavior** that is not already explained by credible baselines and controls.

STAKE is **not**:

- a betting bot;
- a tipster;
- a guaranteed-profit system;
- a "smart money detector";
- an oracle that matches historical benchmark answers;
- a generic sports prediction model unless evidence requires one.

The governing principle is:

> **Measure first. Explain second. Exploit only if the measured structure survives economic and out-of-sample tests.**

---

## 2. Current Research Question

The active question is:

> **Does observable temporal ordering between bookmaker repricing events contain non-random information about subsequent market movement, and if so, does that information survive realistic economic constraints?**

This is deliberately narrower than "can odds movement make money?"

STAKE must answer two separate hypotheses.

### H0-A — Market-structure null

There is no useful, reproducible leader/follower temporal structure beyond what can be explained by synchronized repricing, sampling resolution, random ordering, market-wide shocks, or ordinary consensus movement.

### H0-B — Economic-value null

Even if measurable temporal structure exists, it does not create economically meaningful value after realistic price availability, vig/commission, latency, limits, slippage, selection rules, and execution assumptions.

A result can reject H0-A while failing to reject H0-B. That is a valid research result.

---

## 3. Research Ladder

STAKE progresses through four gates. Do not skip a gate.

```text
GATE 0 — DATA INTEGRITY
        ↓
GATE 1 — TEMPORAL STRUCTURE
        ↓
GATE 2 — PREDICTIVE / PRICE EFFECT
        ↓
GATE 3 — ECONOMIC VALUE
```

### Gate 0 — Data integrity

Can the dataset support the claim being made?

Audit:

- timestamp semantics;
- timestamp resolution;
- duplicate timestamps;
- missing intervals;
- bookmaker coverage;
- fixture coverage;
- ordering ambiguity;
- timezone/clock consistency;
- source-vs-observation provenance when available;
- polling/snapshot artifacts;
- pre-kickoff cutoff integrity.

If the data cannot distinguish two events, STAKE must call them `SIMULTANEOUS` or `AMBIGUOUS`, not invent an ordering.

### Gate 1 — Temporal structure

Measure whether one observable bookmaker movement systematically precedes other movements.

Primary quantities:

- lead-lag delta in seconds;
- follower probability;
- number of followers;
- propagation speed;
- cross-book dispersion before/after;
- simultaneous rate;
- isolated-move rate;
- reversal rate.

### Gate 2 — Predictive / price effect

If temporal ordering exists, test whether it predicts later market behavior.

Primary quantities:

- future consensus displacement;
- movement magnitude;
- persistence;
- reversal;
- closing-line displacement;
- CLV measured from signal time;
- effect size versus controls;
- effect decay by horizon.

### Gate 3 — Economic value

Only after Gates 0–2 survive should STAKE estimate executable value.

Economic evaluation must account for:

- quoted price actually available at signal time;
- vig/commission;
- latency;
- limits;
- slippage;
- execution probability;
- minimum practical edge;
- selection/availability bias;
- realistic stake assumptions.

Positive CLV is evidence of price quality, **not proof of profit**.

Positive historical ROI is not proof of durability.

---

## 4. Market-Scope Strategy

STAKE will use a **controlled cross-market comparison**, not a permanent assumption that one sport is easier.

Initial market candidates:

1. **EPL 1X2** — efficient-market control/benchmark.
2. **English Championship 1X2** — secondary-market comparison.
3. **Men's Grand Slam tennis match winner** — clean two-outcome comparison.

These are hypotheses about research suitability, not conclusions.

Do not assume:

- tennis is inefficient because it has two outcomes;
- best-of-five automatically creates better signal;
- secondary football leagues are profitable;
- favorites winning frequently implies market inefficiency;
- NBA/NFL/EPL are impossible to exploit;
- in-play is better before timestamp/provenance integrity is established.

### Selection rule

A market earns priority only when its data demonstrates:

1. sufficient timestamp resolution;
2. sufficient bookmaker coverage;
3. measurable temporal ordering;
4. measurable effect size;
5. acceptable decay;
6. credible CLV opportunity;
7. plausible execution conditions.

A softer-sounding market does not outrank a harder market without evidence.

---

## 5. The "Smart Money" Rule

"Smart money" is an **unobservable explanation**, not a raw feature.

Never infer:

```text
odds moved → smart money entered
```

Instead observe:

```text
Book A repriced
    ↓
Book B/C/D repriced later
    ↓
market converged
    ↓
new consensus persisted/reversed
    ↓
close moved
```

Only then may STAKE classify an event as a:

- `PRICE_DISCOVERY_CANDIDATE`;
- `INFORMED_MONEY_CANDIDATE`;
- `LEADER_FOLLOWER_EVENT`;
- `PERSISTENT_CONVERGENCE`;
- `REVERSAL_EVENT`;
- `ISOLATED_BOOK_EVENT`.

These are research classifications, never causal proof.

Financial-market language such as pressure, flow, momentum, and price discovery is permitted as an analogy, but must not be treated as evidence that sports markets operate identically to exchange order books.

---

## 6. Temporal Causality: Required Measurement

The previous coarse classification of movement timing is insufficient for the central experiment.

A result such as:

```text
OVERLAPPING = 5,119
POST_LEADER = 12
```

does **not** establish causality. It may simply reflect timestamp resolution or bucket construction.

The required representation is continuous where the data permits it:

```text
leader_time = t0
follower_time = t1
lead_lag_seconds = t1 - t0
```

For each candidate leader, preserve:

- exact available timestamp;
- bookmaker;
- market/selection;
- pre-move quote;
- post-move quote;
- direction;
- movement magnitude;
- next-book timestamps;
- follower deltas;
- timestamp-resolution metadata.

When the timestamp granularity cannot distinguish events, use `SIMULTANEOUS`/`AMBIGUOUS`.

Do not manufacture sub-second or second-level ordering from minute-level observations.

---

## 7. Data Provenance Contract

STAKE must distinguish the following clocks whenever the source data provides them:

```text
SOURCE_EVENT_TIME       = when the bookmaker/source says the quote changed
OBSERVATION_TIME         = when STAKE observed/recorded the quote
INGESTION_TIME           = when the record entered the local pipeline
```

Current public/sample AH-04 data exposes one timestamp field. Until a source/posting clock is available, STAKE must treat that timestamp as **observation timestamp**, not proven bookmaker-event timestamp, unless the dataset documentation establishes otherwise.

This matters because a first observed quote can be a first observation of an already-changed market, not the true first market mover.

Every experiment must document which clock it uses.

---

## 8. Event Definition

A candidate movement event must be defined without looking into the future.

At signal time `t0`, STAKE may use only data available at or before `t0`.

The event record should include:

```text
fixture
market
selection/side
bookmaker
signal_time
previous_time
movement_direction
movement_size
probability_change (if valid)
local_book_count
pre_event_dispersion
```

Future follower movements, closing prices, match result, and future news cannot be used to decide that the event occurred.

A leader is the **first reliably observable qualifying movement** under the preregistered rule, not the bookmaker with the biggest eventual movement.

---

## 9. Leader / Follower Experiment

The first clean leader/follower experiment should compare:

### Treatment

Detected first mover under the fixed event definition.

### Controls

1. Random-bookmaker leader.
2. Randomized leader timestamp where valid.
3. Consensus movement without leader identification.
4. Simultaneous movement control.
5. Isolated-book movement control.
6. Time-shuffled/null sequence where valid.

The primary outcome is **subsequent market behavior**, not match outcome.

Candidate horizons should be fixed before evaluation, for example:

```text
+5s / +15s / +30s / +60s / +180s / close
```

The actual horizons must be limited by measured timestamp resolution. If the dataset cannot support +5s, that horizon is `NOT MEASURABLE`, not zero.

---

## 10. Effect Size and Decay

STAKE must report effect size in market units, not only p-values.

Examples:

- probability displacement in percentage points;
- odds displacement in decimal odds;
- basis-point-equivalent movement where appropriate;
- CLV in price/probability units;
- follower count/rate;
- seconds of lead/lag;
- persistence duration.

For each signal family, measure decay:

```text
signal
  ↓
5s
15s
30s
60s
180s
close
```

A tiny statistically significant effect that disappears before any realistic execution window is not an economic signal.

Do not choose a favorable horizon after inspecting the results without declaring it as exploratory and validating it separately.

---

## 11. CLV and Economic Evaluation

CLV is downstream of temporal structure, but its definition must be prepared before Gate 2 begins.

Signal-time price is the price actually available at the signal definition.

Closing price is the preregistered closing reference.

STAKE must separately report:

```text
TEMPORAL STRUCTURE
PREDICTIVE MARKET EFFECT
CLV
EXECUTION ASSUMPTIONS
ROI
```

Do not use an arbitrary rule such as "CLV below 1% means failure." Economic thresholds must be derived from the actual market, price convention, vig/commission, latency, limits, and execution assumptions.

---

## 12. Pre-Registration Discipline

Before final evaluation of a market/experiment, record:

- market and season/date range;
- data source;
- timestamp interpretation;
- minimum timestamp resolution;
- event threshold;
- leader definition;
- follower window;
- horizons;
- primary outcome;
- controls;
- train/validation/test split if applicable;
- CLV definition;
- execution assumptions;
- economic cost assumptions;
- statistical method;
- decision rule.

Exploratory changes are allowed, but must be labeled exploratory and cannot silently become confirmatory results.

---

## 13. Out-of-Sample Requirement

No claim of durable value may rely only on the sample used to discover the signal.

Preferred validation:

```text
discovery period
      ↓
freeze definition
      ↓
held-out period
      ↓
final evaluation
```

Where data volume permits, use chronological validation rather than random row splitting because market observations are temporally dependent.

---

## 14. Falsification Rules

STAKE actively tries to kill every hypothesis.

A signal is weakened or rejected if it disappears under credible controls, randomization, held-out data, or realistic costs.

Mandatory checks where applicable:

- random leader identity;
- timestamp shuffling;
- bookmaker-order randomization;
- simultaneous classification;
- isolated-book control;
- simple consensus baseline;
- out-of-sample validation;
- leakage audit;
- cost/latency sensitivity.

Negative results are first-class results.

---

## 15. Existing AH-04 Track

AH-04 remains the current football market laboratory.

Relevant components include:

- `stake/ah04.py` — temporal window construction;
- `stake/ah04_metrics.py` — probability pressure/displacement primitives;
- `stake/ah04_v5.py` — local movement/event primitives;
- `scripts/run_ah04_v5.py` — V5 scanner;
- `scripts/run_ah04_v5_1.py` — V5.1 scanner;
- `tests/test_ah04.py` — temporal-window tests.

The current pressure threshold remains `0.015` unless a separately documented experiment changes it.

Do not lower thresholds merely to increase event count.

The current AH-04 sample path is:

```text
data/raw/ah04/sample/sample/EPL/2024-2025
```

Raw data remains gitignored.

---

## 16. Existing Experiment Record

Historical results remain part of the research record:

- O/U-01 simple goal model — failed.
- O/U-02 model/market disagreement — failed.
- AH-00 market baseline — no trivial AH edge.
- AH-01 handicap-gap probe — failed/inconclusive.
- AH-02 exact Poisson AH settlement — failed.
- AH-03 opening→closing reaction — failed; approximately 51.77% directional accuracy across 1,835 observations.
- AH-04 provenance feasibility gate — established the need to treat timestamp/provenance integrity explicitly.

These results do not prove that every sports market is efficient. They constrain what STAKE should build next.

---

## 17. Current V5/V5.1 Interpretation

V5/V5.1 successfully produces local movement primitives/events, but event production is not evidence of predictive value.

The recent temporal-causality output showing thousands of `OVERLAPPING` observations and only a small number of `POST_LEADER` observations must be treated as a **measurement-resolution warning**, not a causal discovery.

Before a V6 leader/follower claim, STAKE must establish:

1. timestamp resolution;
2. ordering reliability;
3. exact leader rule;
4. follower window;
5. control construction;
6. effect-size measurement.

---

## 18. Minimal Architecture

The project should remain intentionally small:

```text
RAW DATA
   ↓
PROVENANCE / TIMESTAMP AUDIT
   ↓
NORMALIZATION
   ↓
MARKET EVENTS
   ↓
TEMPORAL ORDERING
   ↓
LEADER/FOLLOWER TEST
   ↓
CONTROLS
   ↓
EFFECT + DECAY
   ↓
CLV
   ↓
ECONOMIC TEST
   ↓
OUT-OF-SAMPLE RESULT
   ↓
RESEARCH REPORT
```

Do not create infrastructure for layers that the current evidence does not require.

Every new module must answer a named research question and be demonstrated on historical data.

---

## 19. Current Research Program — 2026-09-11

### Phase 0 — Timestamp/provenance audit

**Status: BLOCKED ON LOCAL RAW DATA ACCESS FOR EXECUTION.**

The repository contains the code but the public/sample raw dataset is intentionally gitignored. The audit must be run against the user's local dataset.

Required outputs:

- rows inspected;
- unique timestamp resolution;
- duplicate timestamp rate;
- per-book timestamp spacing;
- cross-book same-timestamp rate;
- minimum/median/percentile inter-observation gaps;
- bookmaker coverage;
- fixture coverage;
- ordering ambiguity rate;
- whether +5s/+15s/+30s/+60s horizons are measurable.

### Phase 1 — Clean leader/follower experiment

Only after Phase 0 passes.

Use one clean market first. EPL 1X2 remains the control/benchmark because it provides a hard-market reference. Do not abandon it merely because it is likely efficient.

### Phase 2 — Controlled market comparison

If Phase 1 reveals a measurable structure, apply the same preregistered methodology to:

- EPL 1X2;
- Championship 1X2;
- Men's Grand Slam match winner.

No sport-specific tuning until the common test is complete.

### Phase 3 — CLV and economic evaluation

Only for signal families that survive Phase 1/2.

### Phase 4 — Out-of-sample validation

Freeze definitions before evaluating the held-out period.

### Phase 5 — Decision

Exactly one of:

```text
KILL
RETAIN AS RESEARCH FINDING
REDIRECT TO SOFTER MARKET
PROCEED TO ECONOMIC TEST
```

---

## 20. Timebox

The current movement-research branch is timeboxed to approximately **4–6 weeks of focused work**, not an open-ended taxonomy project.

The objective is not to enumerate every possible movement pattern.

The objective is to determine whether one clean, measurable market structure survives:

```text
integrity
→ structure
→ effect
→ controls
→ economics
→ out-of-sample
```

If it does not, stop expanding that branch.

---

## 21. Required Experiment Report

Every meaningful experiment must report:

```text
QUESTION:
HYPOTHESIS:
DATASET:
DATA INTEGRITY:
SAMPLE SIZE:
EVENT DEFINITION:
TIMESTAMP RESOLUTION:
CONTROL(S):
PRIMARY EFFECT:
EFFECT SIZE:
DECAY:
CLV:
EXECUTION ASSUMPTIONS:
ROI:
OUT-OF-SAMPLE:
FAILURE CASES:
INTERPRETATION:
DECISION:
NEXT ACTION:
```

Unavailable metrics must be reported as `NOT MEASURED` or `NOT MEASURABLE`, never inferred.

---

## 22. Definition of Success

STAKE succeeds when it can make a claim like:

> Under these exact observable conditions, using only information available at signal time, the market subsequently behaved differently from specified controls, the effect survived held-out validation, and the remaining economic assumptions are explicit.

STAKE fails when its strongest claim is:

> The odds moved and the eventual result agreed, therefore smart money knew the result.

The first is research. The second is storytelling.

**STAKE is committed to the first.**
