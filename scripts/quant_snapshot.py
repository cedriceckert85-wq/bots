# -*- coding: utf-8 -*-
"""Naechtliche Quant-Datenpipeline fuer SOLID und RISK (Phase 0).

Berechnet aus Yahoo-Tageskerzen alle Kennzahlen, die die Entscheider-Agenten
brauchen (sie selbst koennen keine Preis-APIs erreichen und rechnen NIE selbst):
12-1-Momentum, 52-Wochen-Hoch-Naehe, SMA200-Status, ATR14, Volumen-Ratio,
Dollar-Volumen sowie Markt-Regime (SPY/QQQ vs. SMA200 mit Hysterese, VIX).
Output: data/quant_snapshot.json — die einzige Wahrheitsquelle der Entscheider.
Fail-closed: Ticker mit Datenfehlern erscheinen unter "fehler" statt mit
Phantomwerten im Ranking.
"""
import json
import os
import time
import datetime
import urllib.request
import urllib.parse

UNIVERSUM = [
    # Mega/Large Caps (liquide S&P-500-Auswahl, Phase 0 — statisch kuratiert)
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "TSLA", "BRK-B", "LLY",
    "JPM", "V", "MA", "UNH", "XOM", "CVX", "HD", "COST", "WMT", "PG",
    "JNJ", "ABBV", "MRK", "ORCL", "CRM", "ADBE", "AMD", "QCOM", "TXN", "INTC",
    "NFLX", "DIS", "CMCSA", "PEP", "KO", "MCD", "NKE", "SBUX", "TMO", "ABT",
    "CAT", "DE", "BA", "GE", "HON", "UNP", "UPS", "RTX", "LMT", "NOC",
    "GS", "MS", "BAC", "WFC", "C", "BLK", "SCHW", "AXP", "PYPL", "INTU",
    "NOW", "PANW", "ANET", "MU", "LRCX", "AMAT", "KLAC", "SNPS", "CDNS", "CEG",
    "VST", "NEE", "DUK", "SO", "LIN", "FCX", "NEM", "COP", "SLB", "EOG",
    "HPE", "IBM", "CSCO", "T", "VZ", "TMUS", "BKNG", "ABNB", "UBER", "PLTR",
]
ETFS = ["SPY", "QQQ", "IWM", "TQQQ"]
INDIZES = ["^VIX", "^IRX"]


def kerzen(symbol, range_="2y", versuche=4):  # 2 Jahre: 12-1-Momentum braucht >=252 Handelstage
    # Robust gegen transiente Yahoo-Aussetzer (429/leere Antwort): mehrfach mit Backoff
    # versuchen. Eine LEERE Serie zaehlt als Fehlschlag -> Retry (sonst landen still
    # Phantom-nulls im Snapshot und die Bots machen grundlos KEIN TRADE).
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/"
           + urllib.parse.quote(symbol) + f"?interval=1d&range={range_}")
    letzter_fehler = None
    for n in range(versuche):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                d = json.load(r)
            res = d["chart"]["result"][0]
            q = res["indicators"]["quote"][0]
            out = []
            for i, t in enumerate(res["timestamp"]):
                o, h, l, c, v = q["open"][i], q["high"][i], q["low"][i], q["close"][i], q["volume"][i]
                if None in (o, h, l, c):
                    continue
                out.append({"t": datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),
                            "o": o, "h": h, "l": l, "c": c, "v": v or 0})
            if out:
                return out
            letzter_fehler = ValueError("leere Kerzenserie")
        except Exception as e:
            letzter_fehler = e
        if n < versuche - 1:
            time.sleep(2 + 3 * n)  # 2s, 5s, 8s Backoff
    raise letzter_fehler or ValueError("keine Daten")


def sma(werte, n):
    return sum(werte[-n:]) / n if len(werte) >= n else None


def atr14(k):
    if len(k) < 15:
        return None
    trs = []
    for i in range(-14, 0):
        h, l, cv = k[i]["h"], k[i]["l"], k[i - 1]["c"]
        trs.append(max(h - l, abs(h - cv), abs(l - cv)))
    return sum(trs) / 14


def kennzahlen(k):
    closes = [x["c"] for x in k]
    letzte = k[-1]
    erg = {"close": round(letzte["c"], 2), "datum": letzte["t"]}
    # 12-1-Momentum: Rendite von t-252 bis t-21 (Skip des letzten Monats)
    if len(closes) >= 252:
        erg["mom12_1"] = round((closes[-21] / closes[-252] - 1) * 100, 2)
    else:
        erg["mom12_1"] = None
    hoch52w = max(x["h"] for x in k[-252:]) if len(k) >= 50 else None
    erg["dist52wHochPct"] = round((letzte["c"] / hoch52w - 1) * 100, 2) if hoch52w else None
    s200 = sma(closes, 200)
    erg["sma200"] = round(s200, 2) if s200 else None
    erg["ueberSma200"] = bool(s200 and letzte["c"] > s200)
    a = atr14(k)
    erg["atr14"] = round(a, 2) if a else None
    erg["atrPct"] = round(a / letzte["c"] * 100, 2) if a else None
    vol20 = sma([x["v"] for x in k], 20)
    erg["volRatio"] = round(letzte["v"] / vol20, 2) if vol20 else None
    erg["dollarVol20dMio"] = round(vol20 * letzte["c"] / 1e6, 1) if vol20 else None
    return erg


def main():
    snapshot = {
        "generatedAtUtc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "asOf": None,
        "ticker": {},
        "etfs": {},
        "regime": {},
        "fehler": [],
    }
    for sym in UNIVERSUM:
        try:
            k = kerzen(sym)
            if not k:
                raise ValueError("keine Kerzen")
            snapshot["ticker"][sym] = kennzahlen(k)
        except Exception as e:
            snapshot["fehler"].append(f"{sym}: {e}")
    for sym in ETFS + INDIZES:
        try:
            k = kerzen(sym)
            snapshot["etfs"][sym.replace("^", "")] = kennzahlen(k)
        except Exception as e:
            snapshot["fehler"].append(f"{sym}: {e}")

    spy = snapshot["etfs"].get("SPY", {})
    qqq = snapshot["etfs"].get("QQQ", {})
    vix = snapshot["etfs"].get("VIX", {})
    snapshot["asOf"] = spy.get("datum")
    # Regime mit 2%-Hysterese-Zonen (Details/Verwendung: SPEC_SOLID R-Layer, SPEC_RISK Engine C)
    def zone(e):
        if not e.get("sma200"):
            return "unbekannt"
        rel = e["close"] / e["sma200"] - 1
        if rel > 0.02:
            return "risk_on"
        if rel < -0.02:
            return "risk_off"
        return "neutral"
    snapshot["regime"] = {
        "spyZone": zone(spy),
        "qqqZone": zone(qqq),
        "vixClose": vix.get("close"),
        "vixUnter25": bool(vix.get("close") and vix["close"] < 25),
    }
    # Momentum-Ranking (Top-Dezil-Hilfe fuer SOLID, Leader-Liste fuer RISK)
    rangliste = sorted(
        [(s, t["mom12_1"]) for s, t in snapshot["ticker"].items()
         if t["mom12_1"] is not None and t["ueberSma200"] and (t["dollarVol20dMio"] or 0) > 50],
        key=lambda x: x[1], reverse=True)
    snapshot["momentumRanking"] = [{"ticker": s, "mom12_1": m} for s, m in rangliste[:25]]
    volSpikes = sorted(
        [(s, t["volRatio"]) for s, t in snapshot["ticker"].items()
         if (t["volRatio"] or 0) >= 2.0],
        key=lambda x: x[1], reverse=True)
    snapshot["volumenSpikes"] = [{"ticker": s, "volRatio": v} for s, v in volSpikes]

    # --- SANITY-GATE (Haertung 13.06.) -------------------------------------
    # Verhindert, dass ein kaputter Lauf (Yahoo-Aussetzer -> fast alles null)
    # einen GUTEN Snapshot ueberschreibt. Bei zu schlechter Datenqualitaet:
    # bestehenden Snapshot NICHT anfassen und mit Exit 1 abbrechen -> die
    # GitHub-Action faellt sichtbar (Alarm-Mail), die Bots laufen am alten
    # (dann veralteten) Snapshot fail-closed = KEIN falscher Trade.
    datei = "data/quant_snapshot.json"
    gueltig = sum(1 for t in snapshot["ticker"].values() if t.get("mom12_1") is not None)
    mindest = max(40, int(0.5 * len(UNIVERSUM)))
    schlecht = gueltig < mindest or not snapshot["momentumRanking"] or not snapshot["asOf"]
    if schlecht and os.path.exists(datei):
        print(f"FEHLER Datenqualitaet: nur {gueltig}/{len(UNIVERSUM)} Ticker mit mom12_1, "
              f"Ranking={len(snapshot['momentumRanking'])}, asOf={snapshot['asOf']}, "
              f"{len(snapshot['fehler'])} Fehler. Bestehender Snapshot bleibt unangetastet.")
        raise SystemExit(1)

    with open(datei, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Snapshot {snapshot['asOf']}: {len(snapshot['ticker'])} Ticker, "
          f"{gueltig} mit mom12_1, {len(snapshot['fehler'])} Fehler, "
          f"Regime {snapshot['regime']['spyZone']}")
    if schlecht:
        print("WARNUNG: Datenqualitaet schwach, aber kein alter Snapshot vorhanden -> "
              "geschrieben und Exit 1 zur Sichtbarkeit.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
