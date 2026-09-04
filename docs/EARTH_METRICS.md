# Earth Health Dashboard: Data Sourcing & Database Design

This document explains how the `/earth-metrics` API and the frontend's
`/earth-health` page get their data: the database schema, where every
number comes from, and the known limitations of each metric.

Previously this dashboard was hardcoded mock data in the frontend
(`pages/api/health-check.ts` in `alter-app`). All 14 of the original
metrics are now backed by real, cited historical data in this database.

## Database Design

Three tables, added in `db/migrations/008_create_earth_metrics_tables.sql`:

```
data_sources                earth_metrics                 earth_metric_readings
------------------          ------------------------       ------------------------
id (uuid, pk)                id (varchar, pk - slug)        id (uuid, pk)
name                         category                       metric_id (fk -> earth_metrics.id)
organization                 name / simplified_name          reading_date (date)
url                          icon, unit                      value (float)
description                  target_value / target_desc      source_id (fk -> data_sources.id)
retrieved_at                 description / action_info       created_at
created_at                   higher_is_worse (bool)
                              warning_threshold (nullable)
                              critical_threshold (nullable)
                              display_order
                              is_active
```

**Why three tables instead of one:**

- `earth_metrics` holds the *static* metadata for a dashboard card - the
  copy, unit, and thresholds. This rarely changes and is analogous to the
  old hardcoded mock objects.
- `earth_metric_readings` holds the *time series* - one row per
  `(metric_id, reading_date)`. This is what makes the history graphs
  possible, and it's what's actually new compared to the old mock data
  model (which only ever had a single `currentValue`).
- `data_sources` is normalized out on its own because several metrics
  share the same publisher (e.g. every OWID-sourced metric points back
  to the same handful of source rows), and because a reading's
  provenance needs to be independently citable/inspectable - each
  reading carries its own `source_id`, so a metric that later blends
  multiple sources (see Ocean Plastic below) can attribute each point
  correctly instead of one blanket citation per metric.

**Trend/status are computed, not stored.** `GET /earth-metrics` derives
`current_value`, `trend`, `trend_direction`, and `status` from the
readings at request time (see `_derive_trend_and_status` in
`app/api/endpoints/earth_metrics.py`):

- **Trend**: compares the latest reading to the reading from ~10 years
  earlier (or the earliest available if the series is shorter). A <0.5%
  relative change is "stable"; otherwise "up"/"down", combined with
  `higher_is_worse` to produce "worsening"/"improving".
- **Status**: uses `warning_threshold`/`critical_threshold` if set on the
  metric (all 14 metrics currently have these); otherwise falls back to
  a distance-from-`target_value` heuristic.

**Known limitation of the trend heuristic:** it's a generic "~10 years
ago vs. now" comparison, which works well for annual series but can look
counterintuitive on sparse/epoch-based data. For example, coral reef
cover shows "improving" because its nearest available comparison point
(1998, the year of a mass bleaching crash) happens to be a local minimum
- the metric is genuinely designated a real recovery *since 1998*, but
that reads oddly next to the fact that global coral cover is still well
below its 1978-1997 baseline. The underlying numbers and citations are
accurate; only the auto-generated trend label can be misleading for
irregularly-spaced series. Worth keeping in mind before doing the design
pass on trend arrows/colors.

## API

- `GET /api/v1/earth-metrics` - all active metrics with latest value,
  trend, status, and a `source` object (name/org/url/retrieved_at).
- `GET /api/v1/earth-metrics/{id}/history` - full reading series for one
  metric, for the graph.

Both are public (no auth), matching the "public read" pattern used for
comments - this data is meant to be browsable and citable without a
login.

The frontend (`alter-app`) proxies both through `pages/api/health-check.ts`
and `pages/api/earth-metric-history.ts`, merging live backend metrics
with (currently zero) leftover static ones by id.

## Seeding

`db/seeds/seed_earth_metrics.py` is the single source of truth for all
metric definitions and readings. It's idempotent: `_get_or_create_source`
and `_upsert_metric` upsert by name/id, and `_upsert_readings` only
inserts readings for dates that don't already exist, so re-running it
(e.g. to append a newer year) is always safe.

## Data Sourcing, Metric by Metric

| Metric ID | Source | Organization | Coverage | Resolution | Notes |
|---|---|---|---|---|---|
| `co2-level` | [NOAA GML Mauna Loa](https://gml.noaa.gov/ccgg/trends/) | NOAA Global Monitoring Laboratory | 1959-2025 | Annual | Instrumental record (Keeling Curve). Pre-1959 ice-core data not yet seeded (see Follow-ups). |
| `global-temp` | [NASA GISTEMP v4](https://data.giss.nasa.gov/gistemp/) | NASA GISS | 1880-2025 | Annual | Anomaly vs. 1951-1980 baseline. |
| `methane-level` | [NOAA GML CH4](https://gml.noaa.gov/ccgg/trends_ch4/) | NOAA Global Monitoring Laboratory | 1984-2025 | Annual | Same collection network as CO2. |
| `arctic-ice` | [OWID / NSIDC Sea Ice Index](https://ourworldindata.org/grapher/arctic-sea-ice) | NSIDC | 1979-2025 | Annual | September (summer) minimum extent - satellite era only, can't go back further. |
| `ocean-ph` | Hawaii Ocean Time-series, Station ALOHA | Univ. of Hawai'i / NSF | 1988-2020 | Decadal | Only 4 points (1988/2000/2010/2020) - HOT-DOGS is an interactive query tool, not a flat downloadable file, so these are the values a research pass surfaced from the published record rather than something fetched programmatically. Medium confidence; worth re-verifying against a primary export if this metric gets more design prominence. |
| `sea-level` | [OWID / Church & White 2011 + UHSLC](https://ourworldindata.org/grapher/sea-level) | Church & White / UHSLC | 1880-2020 | Annual (from quarterly) | mm relative to the 1993-2008 average - a cumulative level, not a rate. Unit differs from the original mock ("mm/year") on purpose, because a rate framing doesn't match what this dataset measures. |
| `coral-reefs` | GCRMN *Status of Coral Reefs of the World: 2020* | GCRMN / ICRI / UNEP | 1978-2019 | 4 epoch points | GCRMN publishes validated multi-year epoch assessments (baseline, 1998 bleaching, 2009 recovery, 2018 post-bleaching), not an annual series. Years used are representative midpoints of each reported epoch, not actual survey dates. |
| `ocean-plastic` | Jambeck et al. 2015, *Science*, [DOI:10.1126/science.1260352](https://doi.org/10.1126/science.1260352) | Peer-reviewed study | 2010 only | Single point | **No continuous time series exists for this metric anywhere.** Other published estimates (Lebreton 2017, Borrelle 2020, Meijer 2021) use incompatible scopes (river-only vs. all-aquatic vs. coastal) and would misrepresent a trend if blended together. Deliberately seeded with one cited point rather than a fabricated series - see the docstring in the seed script for the full reasoning and the alternative estimates if this needs revisiting. |
| `forest-cover` | [OWID / FAO Forest Resources Assessment](https://ourworldindata.org/grapher/annual-deforestation) | FAO | 1990-2020 | 5-yearly | FAO's native assessment resolution. Note: this shows net deforestation *improving* over time (declining loss rate) - a real finding from FAO data, differing from the old mock's assumption that it was worsening. |
| `freshwater` | [OWID / UN SDG 6.4.2](https://ourworldindata.org/grapher/freshwater-withdrawals-as-a-share-of-internal-resources) | UN SDG Indicator 6.4.2 | 2000-2023 | Annual | Global aggregate reads as "good" (~17-18%, below the 25% stress threshold) - this masks much more severe regional stress; described as such in the metric's own description text. |
| `wildlife-health` | [OWID / Living Planet Index](https://ourworldindata.org/grapher/global-living-planet-index) | WWF / Zoological Society of London | 1970-2020 | Annual | Indexed to 100 in 1970; latest value (~27) reflects the commonly-cited "~70%+ decline since 1970" figure. |
| `extinction-risk` | [OWID / Red List Index](https://ourworldindata.org/grapher/red-list-index) | IUCN | 1993-2024 | Annual | 1.0 = no species expected to go extinct near-term. |
| `air-quality` | [OWID / PM2.5](https://ourworldindata.org/grapher/pm25-air-pollution) | Health Effects Institute, State of Global Air | 1998-2024 | Annual | Population-weighted global average exposure. |
| `renewable-energy` | [OWID / Share of Electricity from Renewables](https://ourworldindata.org/grapher/share-electricity-renewables) | Ember / Energy Institute | 1900-2025 | Annual | Deliberately uses *electricity* share, not primary-energy share (primary energy is much lower, ~8.6% in 2025, and would read as a much bigger regression from the old mock's 29% than is actually the case - the two numbers measure genuinely different things and shouldn't be conflated). |

## Reliability Notes

- **Every OWID number was pulled as raw CSV via their grapher API
  (`ourworldindata.org/grapher/<slug>.csv?...`) and parsed directly with
  Python** (`csv.DictReader`), not summarized through an LLM. This
  avoids the transcription-error risk that comes with having a model
  read and restate numeric tables.
- **NOAA CO2/CH4 and NASA GISTEMP** were pulled via `WebFetch` against
  their plain-text/CSV endpoints - simple enough tables that extraction
  risk is low, and NOAA's Mauna Loa CO2 numbers were cross-checked
  against well-known public figures (e.g. "CO2 passed 420ppm in 2023")
  during this work.
- **Ocean pH, coral reefs, and ocean plastic** were researched via a
  separate LLM session given a citation-first prompt (see
  `ALTER_RESEARCH/earth-metrics/` if that directory is still around),
  then cross-checked against figures already known before being seeded.
  These carry the lowest confidence of the 14 - not because the sources
  are wrong, but because the exact point values weren't independently
  re-derived from a primary machine-readable export the way the OWID and
  NOAA data was.

## Follow-ups / Known Gaps

1. **Pre-1959 CO2** - ice-core reconstructions (e.g. Law Dome) could
   extend this back toward 1900, but need to be pulled from the primary
   data file directly rather than a secondhand summary.
2. **Ocean pH precision** - try to get a direct machine-readable export
   (e.g. from NOAA NCEI's Ocean Carbon and Acidification Data System)
   instead of the decadal approximations currently seeded.
3. **Design pass** - now that every metric has real history, the
   `/earth-health` page's card design and the trend arrow/status colors
   can be revisited (a Claude Design mockup was the originally discussed
   next step), including deciding how to visually flag the metrics with
   sparse/irregular data (coral reefs, ocean plastic, deforestation)
   differently from the dense annual series.
