# -*- coding: utf-8 -*-
"""Alpaca-Paper-Anbindung fuer SOLID und RISK (Stufe 1).

Erprobte Swing-Agent-Logik, parameterisiert je Bot: platziert neue Journal-Trades
("wartet", US-Symbol) als Bracket-Order (Entry+Stop+Ziel, GTC) und synct Fills.
Stueckzahl = floor(RISIKO_USD / Stop-Distanz). SOLID: 1.000 $, RISK: 2.000 $.
Verfall: Entry >2 Handelstage nicht getriggert -> Order canceln. Zeit-Exit:
Legs canceln + Market-on-Open. Ohne Keys: stiller No-Op je Bot.
"""
import json
import os
import sys
import datetime
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trade_eval import r_multiple, statistik_neu  # noqa: E402

BASE = "https://paper-api.alpaca.markets/v2"
BOTS = [
    {"journal": "data/solid_journal.json", "prefix": "ALPACA_SOLID", "risiko_usd": 1000},
    {"journal": "data/risk_journal.json", "prefix": "ALPACA_RISK", "risiko_usd": 2000},
]


def api(keys, pfad, methode="GET", body=None):
    req = urllib.request.Request(
        BASE + pfad, method=methode,
        headers={"APCA-API-KEY-ID": keys[0], "APCA-API-SECRET-KEY": keys[1],
                 "Content-Type": "application/json"},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            inhalt = r.read().decode()
            return json.loads(inhalt) if inhalt else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{methode} {pfad}: HTTP {e.code} {e.read().decode()[:300]}")


def handelstage(von, bis):
    d = datetime.date.fromisoformat(von)
    ende = datetime.date.fromisoformat(bis)
    n = 0
    while d < ende:
        d += datetime.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def order_anlegen(keys, t, risiko_usd):
    risiko = abs(t["entry"] - t["stop"])
    qty = int(risiko_usd // risiko) if risiko > 0 else 0
    if qty < 1:
        t.setdefault("log", []).append("Alpaca: Stop-Distanz zu gross, qty<1 -> Yahoo-Simulation")
        return
    seite = "buy" if t["richtung"] == "long" else "sell"
    typ = "limit" if t.get("entryTyp", "stop") == "limit" else "stop"
    body = {"symbol": t["ticker"], "qty": str(qty), "side": seite, "type": typ,
            "time_in_force": "gtc", "order_class": "bracket",
            "take_profit": {"limit_price": f"{t['tp']:.2f}"},
            "stop_loss": {"stop_price": f"{t['stop']:.2f}"}}
    body["limit_price" if typ == "limit" else "stop_price"] = f"{t['entry']:.2f}"
    o = api(keys, "/orders", "POST", body)
    t["alpaca"] = {"orderId": o["id"], "qty": qty}
    t.setdefault("log", []).append(f"Alpaca: Bracket-Order platziert ({qty} Stk.)")
    print(f"{t['id']} {t['ticker']}: Bracket {qty} Stk.")


def order_sync(keys, t, risiko_usd):
    heute = datetime.date.today().isoformat()
    o = api(keys, f"/orders/{t['alpaca']['orderId']}?nested=true")
    if t["status"] == "wartet":
        if o["status"] == "filled":
            t["status"] = "offen"
            t["entryFill"] = round(float(o["filled_avg_price"]), 2)
            t["entryDatum"] = o["filled_at"][:10]
        elif o["status"] in ("canceled", "expired", "rejected", "done_for_day"):
            t["status"] = "verfallen"
        elif handelstage(t["datumEmpfehlung"], heute) > 2:
            api(keys, f"/orders/{t['alpaca']['orderId']}", "DELETE")
            t["status"] = "verfallen"
    if t["status"] == "offen":
        if t.get("exitOrderId"):
            eo = api(keys, f"/orders/{t['exitOrderId']}")
            if eo["status"] == "filled":
                t["status"] = "zeit_exit"
                t["exitKurs"] = round(float(eo["filled_avg_price"]), 2)
                t["exitDatum"] = eo["filled_at"][:10]
        else:
            for leg in (o.get("legs") or []):
                if leg["status"] == "filled":
                    t["exitKurs"] = round(float(leg["filled_avg_price"]), 2)
                    t["exitDatum"] = leg["filled_at"][:10]
                    t["status"] = "gewonnen" if leg["type"] == "limit" else "verloren"
                    break
            if (t["status"] == "offen"
                    and handelstage(t["entryDatum"], heute) >= t.get("maxHaltezeitTage", 5)):
                for leg in (o.get("legs") or []):
                    if leg["status"] not in ("filled", "canceled", "expired"):
                        try:
                            api(keys, f"/orders/{leg['id']}", "DELETE")
                        except RuntimeError:
                            pass
                seite = "sell" if t["richtung"] == "long" else "buy"
                eo = api(keys, "/orders", "POST", {
                    "symbol": t["ticker"], "qty": str(t["alpaca"]["qty"]),
                    "side": seite, "type": "market", "time_in_force": "opg"})
                t["exitOrderId"] = eo["id"]
                t.setdefault("log", []).append("Haltedauer erreicht -> MOO-Exit platziert")
    if t["status"] in ("gewonnen", "verloren", "zeit_exit") and "ergebnisR" not in t:
        t["ergebnisR"] = r_multiple(t, t["exitKurs"])
        t["pnlEur"] = round(t["ergebnisR"] * risiko_usd, 2)


def main():
    for bot in BOTS:
        keys = (os.environ.get(bot["prefix"] + "_KEY", ""), os.environ.get(bot["prefix"] + "_SECRET", ""))
        if not keys[0]:
            print(f"{bot['journal']}: keine Keys — uebersprungen.")
            continue
        with open(bot["journal"], encoding="utf-8") as f:
            d = json.load(f)
        vorher = json.dumps(d, sort_keys=True)
        for t in d["trades"]:
            if "." in t.get("yahooSymbol", t["ticker"]):
                continue
            try:
                if t["status"] == "wartet" and "alpaca" not in t:
                    order_anlegen(keys, t, bot["risiko_usd"])
                if "alpaca" in t and t["status"] in ("wartet", "offen"):
                    order_sync(keys, t, bot["risiko_usd"])
            except RuntimeError as e:
                print(f"{t['id']}: {e}")
        d["statistik"] = statistik_neu(d["trades"])
        if json.dumps(d, sort_keys=True) != vorher:
            with open(bot["journal"], "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print(bot["journal"], "aktualisiert (Alpaca).")
        else:
            print(bot["journal"], "unveraendert (Alpaca).")


if __name__ == "__main__":
    main()
