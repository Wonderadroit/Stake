# AH-04 Data Source Qualification

## Purpose

AH-04 tests whether timestamped pre-match information can be followed by measurable Asian Handicap market repricing without look-ahead.

The experiment requires two independent time axes:

1. **Information** — what was known and when it became available.
2. **Market** — handicap line and prices, with timestamps before and after the information event.

No timestamp may be inferred from kickoff, final lineups, scrape time, or a later publication.

## Source A — Fantasy Premier League time-series snapshots

`martgra/fpl-timeseries-data` documents `bootstrap-static` snapshots downloaded every six hours UTC and stored with timestamped filenames. FPL's data dictionary defines `news_added` as the timestamp when news was added and also exposes status and chance-of-playing fields.

A stronger historical recovery is documented by `beeradb/FPL-Armband`: Internet Archive captures were recovered for all six completed seasons 2020/21–2025/26, covering 228/228 gameweeks. Its backfill process selects a crawl strictly before the deadline and then verifies the payload itself to reject post-deadline captures.

**Use:** candidate information-event source.

**Strength:** this provides a defensible point-in-time route instead of reconstructing availability from end-of-season records.

**Limitation:** an FPL timestamp proves when FPL recorded information, not that every bookmaker saw it at that exact instant. AH-04 must keep the information timestamp and market timestamp independent.

## Source B — Timestamped Asian Handicap market history

The strongest public structural candidate currently identified is the Kaggle **European Football Asian Handicap Odds Time-Series** dataset. Its data card states that it contains 7,494 matches across Europe's top five leagues for 2021–2025, including 1,360 EPL matches. It describes approximately 1,500–2,000 timestamped observations per match across 15 bookmakers, with teams, scores, bookmaker, home odds, handicap, away odds, and timestamp.

The public sample contains EPL, La Liga and Serie A rounds 20–22 of 2024/25: 90 matches and approximately 840 KB. The full dataset is described as approximately 700 MB and available on request.

**Use:** candidate timestamped AH market source.

**Strength:** its documented schema contains timestamp + handicap line + both prices, so Stake can measure actual line/price movement rather than inventing a closing handicap line.

**Limitation:** Stake has not yet acquired and verified the sample/full archive locally, and the Kaggle page lists the license as unknown. The full archive therefore cannot yet be treated as an acquired Stake dataset.

## Source C — The Odds API historical odds

The Odds API documents historical odds snapshots from June 2020, with 10-minute snapshots and 5-minute snapshots from September 2022 for featured markets. Its EPL documentation lists handicap and totals as featured markets.

**Use:** potentially strong market-history source for the full 2021/22–2025/26 window.

**Limitation:** historical access is paid. Stake must not assume access until an actual account/API response is available.

## One-fixture qualification protocol

The next gate is deliberately one fixture, not bulk ingestion.

A fixture qualifies only if real source data can produce:

```text
fixtures.csv
    fixture_id
    kickoff_timestamp
    home_team
    away_team

information.csv
    fixture_id
    information_timestamp
    event_type
    event_value

ah_market.csv
    fixture_id
    market_timestamp
    handicap_line
    home_price
    away_price
```

Minimum chronology:

```text
information_timestamp <= decision_timestamp < kickoff_timestamp
market_timestamp <= kickoff_timestamp
```

Then `scripts/run_ah04_window.py` must identify:

```text
latest AH tick BEFORE information event
            ↓
       information event
            ↓
first AH tick AFTER event, still before kickoff
            ↓
latest AH tick BEFORE kickoff
```

The window must be manually inspected before bulk ingestion is written.

## Qualification decision

**AH-04-PROVENANCE-01: PASS (software gate).**

**Information-source gate: PASS candidate.** Historical FPL captures now have a documented point-in-time recovery method and timestamped news/availability fields.

**Market-source gate: NOT YET PASSED.** The Kaggle AH time-series has the required structure, but Stake has not yet acquired and verified the actual sample/full archive in the experiment environment.

**AH-04 historical data gate: NOT YET PASSED.**

No causal market-latency result should be reported until one real fixture passes the complete information → market → kickoff provenance chain.

## Hard rejection rules

- No final starting XI used as an event unless its publication timestamp is independently known.
- No `news` text assigned a timestamp from the scrape time of a later archive.
- No market line reconstructed from price movement alone.
- No post-kickoff market tick included in the pre-match window.
- No post-match player statistics used as information evidence.
- No fabricated or interpolated timestamps.
- No claim that an information timestamp proves bookmaker awareness; it only establishes when the source recorded the information.

## Current next action

Acquire the public AH sample and inspect its actual CSV contents. If one EPL fixture can be joined to a point-in-time FPL information capture, normalize it into Stake's three input contracts and run the existing AH-04 window builder.

Only after one fixture passes this end-to-end provenance test should Stake build a bulk ingestion adapter.
