# AH-04 Data Source Qualification

## Purpose

AH-04 tests whether timestamped pre-match information can be followed by measurable Asian Handicap market repricing without look-ahead.

The experiment requires two independent time axes:

1. **Information** — what was known and when it became available.
2. **Market** — handicap line and prices, with timestamps before and after the information event.

No timestamp may be inferred from kickoff, final lineups, scrape time, or a later publication.

## Source A — Fantasy Premier League time-series snapshots

`martgra/fpl-timeseries-data` documents that the FPL `bootstrap-static` dataset was downloaded every six hours (UTC) and stored as timestamped snapshots. The repository covers the 2020/21-era project and demonstrates the required snapshot architecture.

Relevant fields in FPL player records include `news`, `news_added`, `status`, `chance_of_playing_this_round`, and `chance_of_playing_next_round`.

**Use:** candidate information-event source.

**Limitation:** this source alone does not provide Asian Handicap market ticks and its historical coverage must be matched fixture-by-fixture before it can support the full AH-04 experiment.

## Source B — OddsPapi historical odds

OddsPapi documents `GET /v4/historical-odds`, which returns timestamped historical odds entries through `createdAt`, grouped by fixture, bookmaker, market, and outcome. The documented endpoint accepts a fixture ID and up to three bookmaker filters.

The current documentation states that historical odds are available from January 2026.

**Use:** candidate timestamped market source for fixtures covered by that archive.

**Limitation:** it does not currently satisfy Stake's original five-season market-history requirement because the documented archive begins in January 2026. It can therefore support a narrower 2025/26-season experiment only where the required fixtures and markets are actually covered.

## Source C — The Odds API historical odds

The Odds API documents historical odds snapshots from June 2020, with 10-minute snapshots and 5-minute snapshots from September 2022 for featured markets. Its EPL documentation explicitly lists handicap and totals as featured markets.

**Use:** potentially strong market-history source for the full 2021/22–2025/26 study window.

**Limitation:** historical access is paid. No Stake code should assume access exists until an actual account/API response is available.

## Qualification decision

AH-04 is **not yet cleared for a five-season causal experiment**.

The strongest next path is:

1. Prove one real 2025/26 EPL fixture using an information snapshot with an explicit timestamp.
2. Retrieve the same fixture's timestamped Asian Handicap history from a market provider.
3. Normalize both into Stake's existing `information.csv`, `ah_market.csv`, and `fixtures.csv` contracts.
4. Run `scripts/run_ah04_window.py`.
5. Inspect the resulting before/after/close window manually before scaling.

Only after one fixture passes this end-to-end provenance test should Stake build a bulk ingestion adapter.

## Hard rejection rules

- No final starting XI used as an event unless its publication timestamp is independently known.
- No `news` text assigned a timestamp from the scrape time of a later archive.
- No market line reconstructed from price movement alone.
- No post-kickoff market tick included in the pre-match window.
- No post-match player statistics used as information evidence.
- No fabricated or interpolated timestamps.

## Current gate

**AH-04-PROVENANCE-01: PASS (software gate).**

**AH-04 historical data gate: NOT YET PASSED.**

The software is ready; the next evidence must come from one real timestamped fixture, not another synthetic test.