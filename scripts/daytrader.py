# -*- coding: utf-8 -*-
"""DAYTRADER: 5-Minute Opening Range Breakout paper bot.

Default mode is dry-run. Use --write to append one signal to
data/daytrader_journal.json and --evaluate to update existing paper trades.
No Alpaca, no real orders.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path

from alpaca_common import (
    DONE_STATUSES,
    OPEN_STATUSES,
    api,
    iso_to_utc_hhmm,
    keys_from_env,
    ny_now,
    price,
    qty_for_risk,
)

# Flotte 2.0: Orders NUR ueber das zentrale Risk-Gate (steuerung/pi/bin/order_gate.py).
# Nicht erreichbar -> KEINE Order direkt (fail-safe).
import sys as _sys  # noqa: E402
_GATE_BIN = str(Path(__file__).resolve().parents[3] / "steuerung" / "pi" / "bin")
if _GATE_BIN not in _sys.path:
    _sys.path.insert(0, _GATE_BIN)
try:
    from order_gate import submit_order as _gate_submit  # noqa: E402
except Exception as _e:  # pragma: no cover
    _gate_submit = None
    print(f"WARN order_gate nicht erreichbar ({_e}) -> Orders werden NICHT direkt gesetzt.")


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "quant_snapshot.json"
JOURNAL = ROOT / "data" / "daytrader_journal.json"
ALPACA_PREFIX = "ALPACA_DAYTRADER"
RISK_USD = 350
MAX_TRADES_PER_DAY = 1
MAX_SYMBOLS_TO_SCAN = 30

BLOCKED_TICKERS = {"TQQQ", "SQQQ", "UPRO", "SPXL", "SOXL", "SDS", "SPXU"}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    try:
        from atomwrite import write_atomic as _wa
        _wa(str(path), json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    except Exception:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")


def r2(x: float) -> float:
    return round(float(x), 2)


def yahoo_5m(symbol: str, range_: str = "5d") -> tuple[list[dict], dict]:
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + urllib.parse.quote(symbol)
        + f"?interval=5m&range={range_}&includePrePost=false"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.load(resp)
    result = data["chart"]["result"][0]
    meta = result.get("meta", {})
    quote = result["indicators"]["quote"][0]
    bars: list[dict] = []
    for i, ts in enumerate(result.get("timestamp", [])):
        o = quote["open"][i]
        h = quote["high"][i]
        l = quote["low"][i]
        c = quote["close"][i]
        v = quote["volume"][i]
        if None in (o, h, l, c):
            continue
        t = dt.datetime.fromtimestamp(ts, dt.UTC)
        bars.append({
            "date": t.date().isoformat(),
            "timeUtc": t.strftime("%H:%M"),
            "o": float(o),
            "h": float(h),
            "l": float(l),
            "c": float(c),
            "v": int(v or 0),
        })
    return bars, meta


def latest_session(bars: list[dict]) -> list[dict]:
    if not bars:
        return []
    day = max(b["date"] for b in bars)
    return [b for b in bars if b["date"] == day]


def vwap(bars: list[dict]) -> float | None:
    pv = 0.0
    vol = 0
    for b in bars:
        typical = (b["h"] + b["l"] + b["c"]) / 3.0
        pv += typical * b["v"]
        vol += b["v"]
    return pv / vol if vol > 0 else None


def next_id(journal: dict) -> str:
    nums = []
    for t in journal.get("trades", []):
        tid = str(t.get("id", ""))
        if tid.startswith("D-"):
            try:
                nums.append(int(tid.split("-", 1)[1]))
            except ValueError:
                pass
    return f"D-{(max(nums) + 1 if nums else 1):03d}"


def finished_stats(trades: list[dict]) -> dict:
    done = [t for t in trades if t.get("status") in ("gewonnen", "verloren", "zeit_exit")]
    wins = [t for t in done if t.get("ergebnisR", 0) > 0]
    losses = [t for t in done if t.get("ergebnisR", 0) <= 0]
    streak = worst = 0
    for t in done:
        streak = streak + 1 if t.get("ergebnisR", 0) <= 0 else 0
        worst = max(worst, streak)
    gain = sum(t.get("ergebnisR", 0) for t in wins)
    loss = abs(sum(t.get("ergebnisR", 0) for t in losses))
    n = len(done)
    return {
        "trades": n,
        "gewonnen": len(wins),
        "verloren": len(losses),
        "verfallen": len([t for t in trades if t.get("status") == "verfallen"]),
        "offen": len([t for t in trades if t.get("status") in ("signal", "offen")]),
        "trefferquote": round(len(wins) / n * 100, 1) if n else None,
        "summeR": round(sum(t.get("ergebnisR", 0) for t in done), 2),
        "erwartungswertR": round(sum(t.get("ergebnisR", 0) for t in done) / n, 3) if n else None,
        "profitFactor": round(gain / loss, 2) if loss > 0 else None,
        "aktuelleVerlustserie": streak,
        "groessteVerlustserie": worst,
        "bremseAktiv": streak >= 2,
    }


def candidate_universe(snapshot: dict) -> list[str]:
    tickers = []
    for ticker, data in snapshot.get("ticker", {}).items():
        if ticker in BLOCKED_TICKERS:
            continue
        if not data.get("ueberSma200"):
            continue
        if (data.get("dollarVol20dMio") or 0) < 50:
            continue
        tickers.append(ticker)
    tickers.sort(
        key=lambda t: (
            snapshot["ticker"][t].get("volRatio") or 0,
            snapshot["ticker"][t].get("mom12_1") or 0,
        ),
        reverse=True,
    )
    return tickers[:MAX_SYMBOLS_TO_SCAN]


def analyze_symbol(symbol: str, snapshot_data: dict) -> dict:
    bars_all, meta = yahoo_5m(symbol)
    bars = latest_session(bars_all)
    if len(bars) < 4:
        return {"ticker": symbol, "ok": False, "reason": "weniger_als_4_5m_kerzen"}
    if len(bars) > 8:
        return {"ticker": symbol, "ok": False, "reason": "signalfenster_verpasst"}

    first = bars[0]
    first3 = bars[:3]
    current = bars[-1]
    prev_close = meta.get("chartPreviousClose") or meta.get("previousClose") or snapshot_data.get("close")
    if not prev_close:
        return {"ticker": symbol, "ok": False, "reason": "prev_close_fehlt"}

    approx_daily_shares = None
    if snapshot_data.get("dollarVol20dMio") and snapshot_data.get("close"):
        approx_daily_shares = snapshot_data["dollarVol20dMio"] * 1_000_000 / snapshot_data["close"]
    early_volume = sum(b["v"] for b in first3)
    early_share = early_volume / approx_daily_shares if approx_daily_shares else 0.0
    gap_pct = first["o"] / float(prev_close) - 1.0
    stock_in_play = abs(gap_pct) >= 0.01 or early_share >= 0.08 or (snapshot_data.get("volRatio") or 0) >= 2.0
    if not stock_in_play:
        return {
            "ticker": symbol,
            "ok": False,
            "reason": "nicht_stock_in_play",
            "gapPct": round(gap_pct * 100, 2),
            "earlyVolumeShare": round(early_share * 100, 2),
        }

    vw = vwap(bars)
    if vw is None or current["c"] <= vw:
        return {"ticker": symbol, "ok": False, "reason": "unter_vwap", "vwap": r2(vw or 0), "last": r2(current["c"])}

    buffer = current["c"] * 0.0005
    entry = first["h"] + buffer
    stop = first["l"] - buffer
    risk = entry - stop
    if risk <= 0:
        return {"ticker": symbol, "ok": False, "reason": "ungueltige_range"}
    risk_pct = risk / entry
    if risk_pct < 0.0015 or risk_pct > 0.02:
        return {"ticker": symbol, "ok": False, "reason": "range_risiko_ausserhalb_band", "riskPct": round(risk_pct * 100, 2)}

    target = entry + 2.0 * risk
    already_triggered = any(b["h"] >= entry for b in bars[1:])
    if already_triggered:
        return {"ticker": symbol, "ok": False, "reason": "orb_trigger_bereits_passiert"}
    score = (
        min(40.0, abs(gap_pct) * 1000.0)
        + min(35.0, early_share * 200.0)
        + min(15.0, max(0.0, (current["c"] / vw - 1.0) * 1000.0))
        + min(10.0, (snapshot_data.get("volRatio") or 0) * 3.0)
    )
    return {
        "ticker": symbol,
        "ok": True,
        "score": round(score, 2),
        "sessionDate": bars[0]["date"],
        "entryTyp": "stop",
        "entry": r2(entry),
        "stop": r2(stop),
        "tp": r2(target),
        "crv": 2.0,
        "riskPct": round(risk_pct * 100, 2),
        "gapPct": round(gap_pct * 100, 2),
        "earlyVolumeShare": round(early_share * 100, 2),
        "vwap": r2(vw),
        "last": r2(current["c"]),
        "alreadyTriggered": already_triggered,
        "bars": len(bars),
    }


def trade_today_exists(journal: dict, session_date: str | None = None) -> bool:
    today = session_date or dt.date.today().isoformat()
    return any(t.get("sessionDate") == today for t in journal.get("trades", []))


def make_trade(candidate: dict, journal: dict) -> dict:
    return {
        "id": next_id(journal),
        "datumSignal": dt.datetime.now(dt.UTC).isoformat(),
        "sessionDate": candidate["sessionDate"],
        "ticker": candidate["ticker"],
        "yahooSymbol": candidate["ticker"],
        "richtung": "long",
        "engine": "ORB5",
        "entryTyp": "stop",
        "entry": candidate["entry"],
        "stop": candidate["stop"],
        "tp": candidate["tp"],
        "crv": candidate["crv"],
        "risikoUsd": RISK_USD,
        "status": "signal",
        "score": candidate["score"],
        "gapPct": candidate["gapPct"],
        "earlyVolumeShare": candidate["earlyVolumeShare"],
        "vwap": candidate["vwap"],
        "maxHaltezeitMinuten": 390,
        "createdBy": "daytrader.py",
        "begruendung": (
            f"DAYTRADER ORB5: Stock in Play, Gap {candidate['gapPct']}%, "
            f"Early-Vol {candidate['earlyVolumeShare']}%, Preis ueber VWAP. "
            "Long nur per Opening-Range-Breakout, kein Overnight."
        ),
    }


def r_multiple(trade: dict, exit_price: float) -> float:
    risk = trade["entryFill"] - trade["stop"]
    if risk <= 0:
        return 0.0
    return round((exit_price - trade["entryFill"]) / risk, 2)


def place_alpaca_order(keys: tuple[str, str], trade: dict) -> bool:
    qty = qty_for_risk(trade["entry"], trade["stop"], trade.get("risikoUsd", RISK_USD))
    if qty < 1:
        trade.setdefault("log", []).append("Alpaca: Stop-Distanz zu gross, qty<1")
        return True
    body = {
        "symbol": trade["ticker"],
        "qty": str(qty),
        "side": "buy",
        "type": "stop",
        "stop_price": price(trade["entry"]),
        "time_in_force": "day",
        "order_class": "bracket",
        "take_profit": {"limit_price": price(trade["tp"])},
        "stop_loss": {"stop_price": price(trade["stop"])},
    }
    if _gate_submit is None:
        trade.setdefault("log", []).append("Alpaca: Risk-Gate nicht erreichbar -> kein Order")
        return True
    order = _gate_submit("daytrade", body)
    if not order or not order.get("id"):
        grund = (order or {}).get("reason") or (order or {}).get("gate") or "kein Versand"
        trade.setdefault("log", []).append(f"Alpaca: Order nicht platziert ({grund})")
        return True
    trade["alpaca"] = {
        "orderId": order["id"],
        "qty": qty,
        "mode": "paper_bracket_day",
        "submittedAt": dt.datetime.now(dt.UTC).isoformat(),
    }
    trade.setdefault("log", []).append(f"Alpaca: DAY-Bracket-Order platziert ({qty} Stk.)")
    return True


def flatten_window_active() -> bool:
    now = ny_now()
    return now.weekday() < 5 and now.hour == 15 and now.minute >= 45


def place_flatten_order(keys: tuple[str, str], trade: dict, order: dict) -> bool:
    if trade.get("exitOrderId") or not flatten_window_active():
        return False
    for leg in order.get("legs") or []:
        if leg.get("status") in OPEN_STATUSES:
            try:
                api(keys, f"/orders/{leg['id']}", "DELETE")
            except RuntimeError as exc:
                trade.setdefault("log", []).append(f"Alpaca: Leg-Cancel fehlgeschlagen: {exc}")
    exit_order = _gate_submit("daytrade", {
        "symbol": trade["ticker"],
        "qty": str(trade["alpaca"]["qty"]),
        "side": "sell",
        "type": "market",
        "time_in_force": "day",
    }) if _gate_submit else None
    if not exit_order or not exit_order.get("id"):
        trade.setdefault("log", []).append(
            f"Alpaca: Close-Guard-Exit nicht platziert ({(exit_order or {}).get('reason', 'Gate?')})")
        return False
    trade["exitOrderId"] = exit_order["id"]
    trade.setdefault("log", []).append("Alpaca: Close-Guard Market-Exit platziert")
    return True


def sync_alpaca_trade(keys: tuple[str, str], trade: dict, flatten: bool) -> bool:
    if trade.get("status") == "signal" and "alpaca" not in trade:
        return place_alpaca_order(keys, trade)
    if "alpaca" not in trade:
        return False

    changed = False
    order = api(keys, f"/orders/{trade['alpaca']['orderId']}?nested=true")
    order_status = order.get("status")

    if trade.get("status") == "signal":
        if order_status == "filled":
            trade["status"] = "offen"
            trade["entryFill"] = r2(float(order["filled_avg_price"]))
            trade["entryTimeUtc"] = iso_to_utc_hhmm(order.get("filled_at"))
            trade.setdefault("log", []).append(f"Alpaca: Entry-Fill {trade['entryFill']:.2f}")
            changed = True
        elif order_status in DONE_STATUSES:
            trade["status"] = "verfallen"
            trade.setdefault("log", []).append(f"Alpaca: Entry-Order {order_status}")
            changed = True

    if trade.get("status") == "offen":
        if trade.get("exitOrderId"):
            exit_order = api(keys, f"/orders/{trade['exitOrderId']}")
            if exit_order.get("status") == "filled":
                trade["status"] = "zeit_exit"
                trade["exitKurs"] = r2(float(exit_order["filled_avg_price"]))
                trade["exitTimeUtc"] = iso_to_utc_hhmm(exit_order.get("filled_at"))
                changed = True
        else:
            for leg in order.get("legs") or []:
                if leg.get("status") == "filled":
                    trade["exitKurs"] = r2(float(leg["filled_avg_price"]))
                    trade["exitTimeUtc"] = iso_to_utc_hhmm(leg.get("filled_at"))
                    trade["status"] = "gewonnen" if leg.get("type") == "limit" else "verloren"
                    changed = True
                    break
            if trade.get("status") == "offen" and flatten:
                changed = place_flatten_order(keys, trade, order) or changed

    if trade.get("status") in ("gewonnen", "verloren", "zeit_exit") and "ergebnisR" not in trade:
        trade["ergebnisR"] = r_multiple(trade, trade["exitKurs"])
        trade["pnlUsd"] = r2(trade["ergebnisR"] * trade.get("risikoUsd", RISK_USD))
        changed = True
    return changed


def sync_alpaca_journal(journal: dict, flatten: bool = False) -> bool:
    keys = keys_from_env(ALPACA_PREFIX)
    if not keys:
        print("DAYTRADER: keine Alpaca-Keys - Alpaca-Sync uebersprungen.")
        return False

    changed = False
    journal.setdefault("konto", {})["alpaca"] = True
    journal["konto"]["status"] = f"ALPACA PAPER ({ALPACA_PREFIX})"
    for trade in journal.get("trades", []):
        if "." in trade.get("yahooSymbol", trade.get("ticker", "")):
            continue
        if trade.get("status") not in ("signal", "offen"):
            continue
        try:
            changed = sync_alpaca_trade(keys, trade, flatten) or changed
        except RuntimeError as exc:
            trade.setdefault("log", []).append(f"Alpaca-Sync fehlgeschlagen: {exc}")
            changed = True
    return changed


def evaluate_trade(trade: dict) -> bool:
    if trade.get("alpaca"):
        return False
    if trade.get("status") not in ("signal", "offen"):
        return False
    bars_all, _ = yahoo_5m(trade.get("yahooSymbol", trade["ticker"]))
    bars = [b for b in bars_all if b["date"] == trade["sessionDate"]]
    if len(bars) < 2:
        trade["status"] = "needs_manual_review"
        trade.setdefault("log", []).append("Keine ausreichenden 5m-Kerzen fuer Auswertung")
        return True

    changed = False
    start_index = 1
    if trade["status"] == "signal":
        for i, b in enumerate(bars[1:], start=1):
            if b["h"] >= trade["entry"]:
                fill = max(b["o"], trade["entry"])
                trade["status"] = "offen"
                trade["entryFill"] = r2(fill)
                trade["entryTimeUtc"] = b["timeUtc"]
                trade.setdefault("log", []).append(f"{b['timeUtc']} Entry-Fill {fill:.2f}")
                start_index = i
                changed = True
                break
        else:
            if len(bars) >= 60:
                trade["status"] = "verfallen"
                trade.setdefault("log", []).append("ORB-Entry nicht getriggert")
                return True
            return changed

    if trade["status"] == "offen":
        entry_seen = False
        for b in bars[start_index:]:
            if not entry_seen and trade.get("entryTimeUtc") and b["timeUtc"] < trade["entryTimeUtc"]:
                continue
            entry_seen = True
            stop_hit = b["l"] <= trade["stop"]
            target_hit = b["h"] >= trade["tp"]
            if stop_hit:
                fill = min(b["o"], trade["stop"])
                trade["status"] = "verloren"
                trade["exitKurs"] = r2(fill)
                trade["exitTimeUtc"] = b["timeUtc"]
                changed = True
                break
            if target_hit:
                fill = max(b["o"], trade["tp"])
                trade["status"] = "gewonnen"
                trade["exitKurs"] = r2(fill)
                trade["exitTimeUtc"] = b["timeUtc"]
                changed = True
                break
        if trade["status"] == "offen" and len(bars) >= 60:
            last = bars[-1]
            trade["status"] = "zeit_exit"
            trade["exitKurs"] = r2(last["c"])
            trade["exitTimeUtc"] = last["timeUtc"]
            changed = True
        if trade["status"] in ("gewonnen", "verloren", "zeit_exit"):
            trade["ergebnisR"] = r_multiple(trade, trade["exitKurs"])
            trade["pnlUsd"] = r2(trade["ergebnisR"] * RISK_USD)
    return changed


def evaluate_journal(journal: dict) -> bool:
    changed = False
    for trade in journal.get("trades", []):
        try:
            if evaluate_trade(trade):
                changed = True
        except Exception as exc:
            trade["status"] = "needs_manual_review"
            trade.setdefault("log", []).append(f"Auswertung fehlgeschlagen: {exc}")
            changed = True
    stats = finished_stats(journal.get("trades", []))
    if stats != journal.get("statistik"):
        journal["statistik"] = stats
        changed = True
    return changed


def scan(snapshot: dict, journal: dict) -> dict:
    if journal.get("statistik", {}).get("bremseAktiv"):
        return {"decision": "NO_TRADE", "reasons": ["verlustserien_bremse"], "candidates": []}
    candidates = []
    rejects = []
    for symbol in candidate_universe(snapshot):
        try:
            result = analyze_symbol(symbol, snapshot["ticker"][symbol])
        except Exception as exc:
            result = {"ticker": symbol, "ok": False, "reason": f"fetch_error:{exc}"}
        if result.get("ok"):
            candidates.append(result)
        else:
            rejects.append(result)
    candidates.sort(key=lambda c: c["score"], reverse=True)
    if not candidates:
        return {"decision": "NO_TRADE", "reasons": ["kein_stock_in_play_setup"], "candidates": [], "rejects": rejects[:10]}
    if trade_today_exists(journal, candidates[0]["sessionDate"]):
        return {"decision": "NO_TRADE", "reasons": ["heute_bereits_trade"], "candidates": candidates[:5], "rejects": rejects[:10]}
    return {"decision": "TRADE_CANDIDATE", "candidate": candidates[0], "candidates": candidates[:5], "rejects": rejects[:10]}


def main() -> int:
    parser = argparse.ArgumentParser(description="DAYTRADER ORB paper bot")
    parser.add_argument("--write", action="store_true", help="append one paper signal")
    parser.add_argument("--evaluate", action="store_true", help="evaluate open DAYTRADER trades")
    parser.add_argument("--alpaca", action="store_true", help="place/sync Alpaca paper orders when keys exist")
    parser.add_argument("--flatten", action="store_true", help="close Alpaca paper positions in the 15:45-15:59 ET window")
    args = parser.parse_args()

    snapshot = load_json(SNAPSHOT)
    journal = load_json(JOURNAL)
    eval_changed = False
    if args.evaluate:
        eval_changed = evaluate_journal(journal)

    result = scan(snapshot, journal)
    output = {
        "mode": {"write": args.write, "evaluate": args.evaluate, "alpaca": args.alpaca, "flatten": args.flatten},
        "snapshotAsOf": snapshot.get("asOf"),
        "decision": result["decision"],
        "topCandidates": result.get("candidates", []),
        "reasons": result.get("reasons", []),
        "evalChanged": eval_changed,
    }

    if args.write and result["decision"] == "TRADE_CANDIDATE":
        trade = make_trade(result["candidate"], journal)
        journal.setdefault("trades", []).append(trade)
        journal["konto"]["hinweisLetzterLauf"] = (
            f"DAYTRADER Signal {trade['id']} {trade['ticker']} fuer {trade['sessionDate']} geschrieben. "
            + ("Alpaca-Paper-Order wird versucht." if args.alpaca else "Paper-only, keine Alpaca-Order.")
        )
        journal.setdefault("laufLog", []).append({
            "datum": dt.datetime.now(dt.UTC).isoformat(),
            "aktion": "signal",
            "tradeId": trade["id"],
            "ticker": trade["ticker"],
            "score": trade["score"],
        })
        output["writtenTrade"] = trade
        eval_changed = True
    elif args.write:
        journal["konto"]["hinweisLetzterLauf"] = "DAYTRADER No-Trade: " + ", ".join(result.get("reasons", []))
        journal.setdefault("laufLog", []).append({
            "datum": dt.datetime.now(dt.UTC).isoformat(),
            "aktion": "no_trade",
            "gruende": result.get("reasons", []),
        })
        eval_changed = True

    alpaca_changed = False
    if args.alpaca:
        alpaca_changed = sync_alpaca_journal(journal, flatten=args.flatten)
        output["alpacaChanged"] = alpaca_changed
        if alpaca_changed:
            eval_changed = True

    if eval_changed:
        journal["statistik"] = finished_stats(journal.get("trades", []))
        write_json(JOURNAL, journal)

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
