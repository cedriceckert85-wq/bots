# 08 — Data Contracts und Data Lineage

Zurück: [[00_HOME]] · Verwandt: [[07_MARKET_DATA]], [[09_RESEARCH_PLATFORM]], [[11_ML_ARCHITECTURE]]

Verbindliche Umsetzung des Data-Feed-Contracts aus der Anforderung. Jeder Datenlauf
(Ingestion-Job) erzeugt genau einen Eintrag in `raw_data_manifests` (Schema §3) und legt
die Rohdaten **unverändert und unveränderlich** im Raw Archive ab, bevor irgendeine
Normalisierung stattfindet.

## 1. Grundprinzipien

1. **Raw first, immutable:** Rohantworten (JSON/CSV wie vom Anbieter geliefert) werden
   komprimiert (zstd) und content-addressiert (`sha256`) in Object Storage geschrieben:
   `raw/{provider}/{feed}/{data_type}/{date}/{manifest_id}.json.zst`. Kein Prozess außer
   dem Archiver hat Schreibrechte; Buckets mit Versionierung + Object Lock (Variante B/C).
2. **Feed-Trennung:** `feed` ∈ {`sip`, `iex`, `eod`, …} ist Teil des Primärschlüssels
   jeder Bar-Tabelle. Ein Join über Feeds hinweg ist nur über explizite Views möglich,
   die den Feed als Spalte ausgeben. IEX- und SIP-Bars können **nie** unbemerkt gemischt
   werden, weil jede Query den Feed nennen muss (kein Default).
3. **Fail-closed bei Entitlement-Fehlern:** Liefert der Anbieter einen Berechtigungs-
   oder Downgrade-Fehler (z.B. SIP nicht abonniert), bricht der Job mit
   `IncidentOpened(severity=high)` ab; es wird nicht stillschweigend auf IEX
   zurückgefallen.
4. **Drei Zeitachsen, immer getrennt:** `market_timestamp` (Ereigniszeit an der Börse,
   tz-aware, ET-Quelle → UTC gespeichert), `as_of` (Wissenszeit: ab wann war der Wert dem
   System bekannt/final), `ingested_at` (Systemzeit der Aufnahme). Backtests dürfen nur
   über `as_of` filtern — nie über `market_timestamp` allein (Bitemporalität).
5. **Korrekturen als neue Versionen:** Anbieterkorrekturen (revidierte Bars, Corporate-
   Action-Updates) erzeugen neue Zeilen mit inkrementierter `revision` und eigenem
   `as_of`; alte Zeilen bleiben bestehen. `correction_of` referenziert die ersetzte Zeile.
6. **Semantik-Drift-Wache:** Historische Batch-Daten und Live-Stream-Daten desselben
   Anbieters werden für einen überlappenden Zeitraum täglich verglichen
   (Live-vs-Backfill-Diff-Job); Abweichungen > Toleranz ⇒ Alert
   ([[19_OBSERVABILITY]] Metrik `feed.semantic_drift`).

## 2. Pflicht-Metadaten je Datenlauf (Manifest)

provider, feed, subscription_plan, asset_class, universe_id, data_type,
adjustment_mode (`raw` | `split_adjusted` | `total_return` — Rohspeicherung immer `raw`),
request_ts, market_ts_range, as_of_ts, ingested_at, expected_finalization_delay,
observed_delay, timezone, market_calendar_version, request_params (vollständig, inkl.
Pagination-Cursor), pagination_status, row_count, missing_stats (erwartete vs erhaltene
Bars je Symbol), duplicate_stats, schema_version, raw_hash, normalized_hash,
code_version (git SHA), config_version, correction_status, source_provenance.

## 3. Manifest-Schema (PostgreSQL)

```sql
CREATE TABLE raw_data_manifests (
  manifest_id      UUID PRIMARY KEY,            -- deterministisch: uuid5(provider,feed,data_type,params_hash,as_of)
  provider         TEXT NOT NULL,
  feed             TEXT NOT NULL,
  subscription_plan TEXT NOT NULL,
  asset_class      TEXT NOT NULL,
  universe_id      TEXT NOT NULL REFERENCES universes(universe_id),
  data_type        TEXT NOT NULL,               -- bars_1min | bars_1d | trades | quotes | corp_actions | ...
  adjustment_mode  TEXT NOT NULL DEFAULT 'raw',
  request_ts       TIMESTAMPTZ NOT NULL,
  market_ts_start  TIMESTAMPTZ NOT NULL,
  market_ts_end    TIMESTAMPTZ NOT NULL,
  as_of_ts         TIMESTAMPTZ NOT NULL,
  ingested_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  expected_final_delay_s INT,
  observed_delay_s INT,
  market_calendar_version TEXT NOT NULL,
  request_params   JSONB NOT NULL,
  pagination_status TEXT NOT NULL,              -- complete | truncated | failed
  row_count        BIGINT NOT NULL,
  missing_stats    JSONB NOT NULL,
  duplicate_stats  JSONB NOT NULL,
  schema_version   TEXT NOT NULL,
  raw_hash         TEXT NOT NULL,               -- sha256 der Rohdatei
  normalized_hash  TEXT,                        -- gesetzt nach Normalisierung
  code_version     TEXT NOT NULL,
  config_version   TEXT NOT NULL,
  correction_status TEXT NOT NULL DEFAULT 'original',  -- original | correction | superseded
  source_provenance JSONB NOT NULL,             -- URL/Endpoint, Account-Alias (nie Keys)
  UNIQUE (provider, feed, data_type, raw_hash)
);
CREATE INDEX ON raw_data_manifests (data_type, market_ts_start, market_ts_end);
CREATE INDEX ON raw_data_manifests (as_of_ts);
```

Vollständige Tabellenlandschaft (corporate_actions, feature_definitions, order_intents, …): [[15_ORDER_STATE_MACHINE]] §2; SQL-Definitionen entstehen in `schemas/` (Repo-Struktur [[20_INFRASTRUCTURE]] §6).

## 4. Normalisierte Bar-Tabelle (System of Record: TimescaleDB/Parquet, ADR-007)

```sql
CREATE TABLE bars (
  symbol      TEXT NOT NULL,
  feed        TEXT NOT NULL,        -- 'sip' | 'iex' | 'eod_provider_x'
  timeframe   TEXT NOT NULL,        -- '1min' | '1day'
  market_ts   TIMESTAMPTZ NOT NULL, -- Bar-Open-Zeit, UTC
  open NUMERIC(18,6) NOT NULL, high NUMERIC(18,6) NOT NULL,
  low  NUMERIC(18,6) NOT NULL, close NUMERIC(18,6) NOT NULL,
  volume BIGINT NOT NULL,
  trade_count INT, vwap NUMERIC(18,6),
  as_of       TIMESTAMPTZ NOT NULL,
  revision    INT NOT NULL DEFAULT 0,
  correction_of BIGINT,             -- FK auf ersetzte Zeile
  manifest_id UUID NOT NULL REFERENCES raw_data_manifests(manifest_id),
  PRIMARY KEY (symbol, feed, timeframe, market_ts, revision)
);
-- Partitionierung: Hypertable über market_ts (Chunks 1 Monat für 1min, 1 Jahr für 1day)
```

Adjustierte Reihen (split-/total-return-adjusted) werden **nie gespeichert, sondern
deterministisch on-the-fly** aus `bars(raw)` + `corporate_actions` je `as_of` abgeleitet
(Funktion `adjust(symbol, series, as_of, mode)`), damit eine neue Corporate Action keine
stillen Rückwirkungen erzeugt und jede Adjustierung reproduzierbar versioniert ist.

## 5. Datenqualitäts-Checks (Validation-Stufe, blockierend vor Feature-Zugriff)

| Check | Regel | Aktion bei Verstoß |
|---|---|---|
| Kalender-Vollständigkeit | erwartete Sessions/Bars je Symbol (exchange_calendars-Version im Manifest) | Gap-Report; > 0,1 % fehlende Minute-Bars/Tag ⇒ WARN, fehlende Daily-Bar ⇒ BLOCK |
| OHLC-Konsistenz | low ≤ open,close ≤ high; Werte > 0 | Zeile quarantänisieren, BLOCK bei > 10 Zeilen |
| Ausreißer | |Δclose| > 20 % ohne Corporate Action | Quarantäne + manuelle Prüfung |
| Duplikate | PK-Verletzung / identische Bar unter neuem Manifest | dedupliziert, gezählt in duplicate_stats |
| Stale Feed | letzte Live-Bar älter als 3× Barlänge während Session | `feed.stale` Alert, Risk-Check R-14 blockt Trading |
| Cross-Source-Diff | Daily Close Alpaca vs Zweitquelle > 10 bps | Alert, BLOCK bei > 25 bps ([[07_MARKET_DATA]] §6) |

## 6. Lineage

Jedes Artefakt trägt die Kette seiner Herkunft: `bars.manifest_id` →
`feature_values.dataset_version` → `dataset_versions.input_manifests[]` →
`model_versions.dataset_version` → `predictions.model_version` →
`order_intents.prediction_id` → `fills.order_intent_id`. Damit ist die in
[[19_OBSERVABILITY]] §4 geforderte End-to-End-Trace durch reine FK-Traversierung
möglich; ein CLI-Tool `astra lineage <fill_id>` gibt die vollständige Kette aus.
