# -*- coding: utf-8 -*-
"""CODEX-Challenger fuer SOLID/RISK.

Dry-run by default. Use --write to append exactly one paper-trade to
data/codex_journal.json. No Alpaca, no real orders.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "quant_snapshot.json"
CODEX_JOURNAL = ROOT / "data" / "codex_journal.json"
REFERENCE_JOURNALS = [
    ROOT / "data" / "solid_journal.json",
    ROOT / "data" / "risk_journal.json",
]

RISK_USD = 1500
MAX_OPEN = 4
MAX_NEW_PER_RUN = 1

CLUSTERS = {
    "semis": {"NVDA", "AMD", "AVGO", "QCOM", "TXN", "INTC", "MU", "LRCX", "AMAT", "KLAC", "SNPS", "CDNS"},
    "mega_tech": {"AAPL", "MSFT", "AMZN", "GOOGL", "META", "NFLX", "CRM", "ADBE", "NOW", "PANW", "ANET", "PLTR"},
    "financials": {"JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "AXP", "V", "MA", "PYPL"},
    "industrials": {"CAT", "DE", "BA", "GE", "HON", "UNP", "UPS", "RTX", "LMT", "NOC"},
    "energy_materials": {"XOM", "CVX", "COP", "SLB", "EOG", "LIN", "FCX", "NEM"},
    "utilities_power": {"CEG", "VST", "NEE", "DUK", "SO"},
    "consumer": {"HD", "COST", "WMT", "PG", "PEP", "KO", "MCD", "NKE", "SBUX", "DIS", "CMCSA", "BKNG", "ABNB", "UBER"},
    "healthcare": {"LLY", "UNH", "TMO", "ABT", "JNJ", "ABBV", "MRK"},
    "etf_beta": {"SPY", "QQQ", "IWM", "TQQQ"},
}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def r2(value: float) -> float:
    return round(float(value), 2)


def cluster_for(ticker: str) -> str:
    for name, members in CLUSTERS.items():
        if ticker in members:
            return name
    return "other"


def active_trades(journal: dict) -> list[dict]:
    return [t for t in journal.get("trades", []) if t.get("status") in ("wartet", "offen")]


def active_reference_tickers() -> set[str]:
    tickers: set[str] = set()
    for path in REFERENCE_JOURNALS:
        if not path.exists():
            continue
        try:
            for trade in active_trades(load_json(path)):
                tickers.add(trade["ticker"])
        except Exception:
            continue
    return tickers


def next_id(journal: dict) -> str:
    nums = []
    for trade in journal.get("trades", []):
        tid = str(trade.get("id", ""))
        if tid.startswith("C-"):
            try:
                nums.append(int(tid.split("-", 1)[1]))
            except ValueError:
                pass
    return f"C-{(max(nums) + 1 if nums else 1):03d}"


def gate_status(snapshot: dict, journal: dict) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not snapshot.get("asOf"):
        reasons.append("snapshot_asOf_fehlt")
    regime = snapshot.get("regime", {})
    if regime.get("spyZone") != "risk_on":
        reasons.append(f"spyZone_{regime.get('spyZone', 'unbekannt')}")
    if len(active_trades(journal)) >= MAX_OPEN:
        reasons.append("max_open_erreicht")
    if journal.get("statistik", {}).get("bremseAktiv"):
        reasons.append("verlustserien_bremse")
    return not reasons, reasons


def liquidity_score(dollar_vol_mio: float | None) -> float:
    if dollar_vol_mio is None:
        return 0.0
    return min(100.0, max(0.0, dollar_vol_mio / 500.0))


def proximity_score(dist_52w_high_pct: float) -> float:
    # Sweet spot: close enough to prove leadership, not exact high-chase.
    ideal = -4.0
    return max(0.0, 100.0 - abs(dist_52w_high_pct - ideal) * 8.0)


def volatility_score(atr_pct: float | None) -> float:
    if atr_pct is None:
        return 0.0
    if atr_pct <= 1.0:
        return 55.0
    if atr_pct <= 4.5:
        return 100.0 - abs(atr_pct - 2.5) * 8.0
    return max(0.0, 70.0 - (atr_pct - 4.5) * 12.0)


def reject_reason(ticker: str, data: dict, open_clusters: set[str], open_tickers: set[str]) -> str | None:
    if ticker in open_tickers:
        return "bereits_offen"
    if not data.get("ueberSma200"):
        return "unter_sma200"
    mom = data.get("mom12_1")
    if mom is None or mom < 40:
        return "momentum_unter_40"
    dist = data.get("dist52wHochPct")
    if dist is None or dist < -15 or dist > -0.2:
        return "nicht_im_52w_sweetspot"
    atr_pct = data.get("atrPct")
    if atr_pct is None or atr_pct > 8:
        return "atr_zu_hoch_oder_fehlt"
    vol_ratio = data.get("volRatio")
    if vol_ratio is not None and vol_ratio > 2.5:
        return "buzz_volumen"
    if (data.get("dollarVol20dMio") or 0) < 50:
        return "liquiditaet_unter_50m"
    cluster = cluster_for(ticker)
    if cluster in open_clusters:
        return f"cluster_bereits_offen_{cluster}"
    return None


def build_candidates(snapshot: dict, journal: dict) -> tuple[list[dict], list[dict]]:
    ticker_data = snapshot.get("ticker", {})
    open_tickers = {t["ticker"] for t in active_trades(journal)}
    open_clusters = {cluster_for(t) for t in open_tickers}
    reference_tickers = active_reference_tickers()
    accepted: list[dict] = []
    rejected: list[dict] = []

    for ticker, data in ticker_data.items():
        reason = reject_reason(ticker, data, open_clusters, open_tickers)
        if reason:
            rejected.append({"ticker": ticker, "reason": reason})
            continue

        mom_score = min(100.0, data["mom12_1"])
        prox_score = proximity_score(data["dist52wHochPct"])
        vol_score = volatility_score(data["atrPct"])
        liq_score = liquidity_score(data.get("dollarVol20dMio"))
        ref_penalty = 12.0 if ticker in reference_tickers else 0.0
        score = 0.45 * mom_score + 0.25 * prox_score + 0.15 * vol_score + 0.15 * liq_score - ref_penalty

        close = float(data["close"])
        atr = float(data["atr14"])
        entry = close + 0.25 * atr
        stop = close - 2.25 * atr
        risk = entry - stop
        tp = entry + 2.5 * risk

        accepted.append({
            "ticker": ticker,
            "cluster": cluster_for(ticker),
            "score": round(score, 2),
            "mom12_1": data["mom12_1"],
            "dist52wHochPct": data["dist52wHochPct"],
            "atrPct": data["atrPct"],
            "volRatio": data.get("volRatio"),
            "close": close,
            "atr14": atr,
            "entry": r2(entry),
            "stop": r2(stop),
            "tp": r2(tp),
            "crv": 2.5,
            "maxHaltezeitTage": 12,
            "referencePenalty": ref_penalty,
        })

    accepted.sort(key=lambda c: c["score"], reverse=True)
    return accepted, rejected


def make_trade(candidate: dict, snapshot: dict, journal: dict) -> dict:
    return {
        "id": next_id(journal),
        "datumEmpfehlung": dt.date.today().isoformat(),
        "aktie": candidate["ticker"],
        "ticker": candidate["ticker"],
        "yahooSymbol": candidate["ticker"],
        "richtung": "long",
        "engine": "A",
        "entryTyp": "stop",
        "entry": candidate["entry"],
        "stop": candidate["stop"],
        "tp": candidate["tp"],
        "crv": candidate["crv"],
        "maxHaltezeitTage": candidate["maxHaltezeitTage"],
        "status": "wartet",
        "risikoUsd": RISK_USD,
        "score": candidate["score"],
        "cluster": candidate["cluster"],
        "snapshotAsOf": snapshot.get("asOf"),
        "createdBy": "codex_challenger.py",
        "begruendung": (
            f"CODEX Engine A: Quality-Momentum-Confirmed. Score {candidate['score']}; "
            f"mom12_1 {candidate['mom12_1']}%, 52W-Distanz {candidate['dist52wHochPct']}%, "
            f"ATR {candidate['atrPct']}%, Cluster {candidate['cluster']}. "
            "Entry nur per Bestaetigungs-Stop; kein TQQQ-/Buzz-Duplikat."
        ),
    }


def update_no_trade(journal: dict, snapshot: dict, reasons: list[str], candidates: list[dict]) -> None:
    journal["konto"]["hinweisLetzterLauf"] = (
        f"CODEX No-Trade {dt.date.today().isoformat()} fuer Snapshot {snapshot.get('asOf')}: "
        + ", ".join(reasons)
    )
    journal.setdefault("laufLog", []).append({
        "datum": dt.datetime.now(dt.timezone.utc).isoformat(),
        "snapshotAsOf": snapshot.get("asOf"),
        "aktion": "no_trade",
        "gruende": reasons,
        "topKandidat": candidates[0] if candidates else None,
    })


def main() -> int:
    parser = argparse.ArgumentParser(description="CODEX Challenger dry-run/write")
    parser.add_argument("--write", action="store_true", help="append one paper trade if gates pass")
    args = parser.parse_args()

    snapshot = load_json(SNAPSHOT)
    journal = load_json(CODEX_JOURNAL)
    gates_ok, gate_reasons = gate_status(snapshot, journal)
    candidates, rejected = build_candidates(snapshot, journal)

    summary = {
        "mode": "write" if args.write else "dry-run",
        "snapshotAsOf": snapshot.get("asOf"),
        "regime": snapshot.get("regime", {}),
        "gatesOk": gates_ok,
        "gateReasons": gate_reasons,
        "topCandidates": candidates[:5],
        "rejectedCount": len(rejected),
    }

    if not gates_ok:
        summary["decision"] = "NO_TRADE"
        if args.write:
            update_no_trade(journal, snapshot, gate_reasons, candidates)
            write_json(CODEX_JOURNAL, journal)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if not candidates:
        summary["decision"] = "NO_TRADE"
        summary["gateReasons"] = ["kein_kandidat"]
        if args.write:
            update_no_trade(journal, snapshot, ["kein_kandidat"], candidates)
            write_json(CODEX_JOURNAL, journal)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if MAX_NEW_PER_RUN < 1:
        summary["decision"] = "NO_TRADE"
        summary["gateReasons"] = ["max_new_zero"]
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    trade = make_trade(candidates[0], snapshot, journal)
    summary["decision"] = "TRADE_CANDIDATE"
    summary["trade"] = trade

    if args.write:
        duplicate_snapshot = any(
            t.get("createdBy") == "codex_challenger.py"
            and t.get("snapshotAsOf") == snapshot.get("asOf")
            and t.get("status") in ("wartet", "offen")
            for t in journal.get("trades", [])
        )
        if duplicate_snapshot:
            summary["decision"] = "NO_TRADE"
            summary["gateReasons"] = ["snapshot_bereits_gehandelt"]
            update_no_trade(journal, snapshot, ["snapshot_bereits_gehandelt"], candidates)
        else:
            journal.setdefault("trades", []).append(trade)
            journal["konto"]["hinweisLetzterLauf"] = (
                f"CODEX Trade {trade['id']} {trade['ticker']} fuer Snapshot {snapshot.get('asOf')} "
                f"geschrieben. Paper only, keine Alpaca-Order."
            )
            journal.setdefault("laufLog", []).append({
                "datum": dt.datetime.now(dt.timezone.utc).isoformat(),
                "snapshotAsOf": snapshot.get("asOf"),
                "aktion": "trade",
                "tradeId": trade["id"],
                "ticker": trade["ticker"],
                "score": trade["score"],
            })
        write_json(CODEX_JOURNAL, journal)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
