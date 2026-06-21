# -*- coding: utf-8 -*-
"""Alpaca-Paper-Anbindung fuer SOLID, RISK und CODEX.

Erprobte Swing-Agent-Logik, parameterisiert je Bot: platziert neue Journal-Trades
("wartet", US-Symbol) als Bracket-Order (Entry+Stop+Ziel, GTC) und synct Fills.
Stueckzahl = floor(RISIKO_USD / Stop-Distanz).
Verfall: Entry >2 Handelstage nicht getriggert -> Order canceln. Zeit-Exit:
Legs canceln + Market-on-Open. Ohne Keys: stiller No-Op je Bot.
"""
import json
import math
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alpaca_common import api, keys_from_env, price, qty_for_risk  # noqa: E402
from trade_eval import r_multiple, statistik_neu  # noqa: E402

# Flotte 2.0: Orders NUR ueber das zentrale Risk-Gate (steuerung/pi/bin/order_gate.py).
# Nicht erreichbar (z.B. fremder Cloud-Runner ohne steuerung/) -> KEINE Order direkt
# (fail-safe: lieber Yahoo-Simulation als am Gate vorbei zu handeln).
_GATE_BIN = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "..", "..", "..", "steuerung", "pi", "bin"))
if _GATE_BIN not in sys.path:
    sys.path.insert(0, _GATE_BIN)
try:
    from order_gate import submit_order as _gate_submit  # noqa: E402
except Exception as _e:  # pragma: no cover
    _gate_submit = None
    print(f"WARN order_gate nicht erreichbar ({_e}) -> Orders werden NICHT direkt gesetzt.")


def _gate_name(bot):
    """Bot-Name fuers Gate aus dem Key-Prefix (ALPACA_SOLID -> solid)."""
    return bot["prefix"].replace("ALPACA_", "").lower()


BOTS = [
    {"journal": "data/solid_journal.json", "prefix": "ALPACA_SOLID", "risiko_usd": 1000},
    {"journal": "data/risk_journal.json", "prefix": "ALPACA_RISK", "risiko_usd": 2000, "sizing": "position", "position_pct": 0.30},
    {"journal": "data/codex_journal.json", "prefix": "ALPACA_CODEX", "risiko_usd": 1500},
]


def handelstage(von, bis):
    d = datetime.date.fromisoformat(von)
    ende = datetime.date.fromisoformat(bis)
    n = 0
    while d < ende:
        d += datetime.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def order_anlegen(keys, t, bot):
    risiko_usd = bot["risiko_usd"]
    if bot.get("sizing") == "position":
        acc = api(keys, "/account")
        equity = float(acc.get("equity", 0))
        bp = float(acc.get("buying_power", 0))
        entry = float(t["entry"])
        if entry > 0:
            qty = math.floor(bot["position_pct"] * equity / entry)
            qty = min(qty, math.floor(bp / entry))  # hart durch Buying Power gedeckelt
        else:
            qty = 0
    else:
        qty = qty_for_risk(t["entry"], t["stop"], risiko_usd)
    if qty < 1:
        t.setdefault("log", []).append("Alpaca: Stop-Distanz zu gross, qty<1 -> Yahoo-Simulation")
        return
    seite = "buy" if t["richtung"] == "long" else "sell"
    typ = "limit" if t.get("entryTyp", "stop") == "limit" else "stop"
    body = {"symbol": t["ticker"], "qty": str(qty), "side": seite, "type": typ,
            "time_in_force": "gtc", "order_class": "bracket",
            "take_profit": {"limit_price": price(t["tp"])},
            "stop_loss": {"stop_price": price(t["stop"])}}
    body["limit_price" if typ == "limit" else "stop_price"] = price(t["entry"])
    if _gate_submit is None:
        t.setdefault("log", []).append("Alpaca: Risk-Gate nicht erreichbar -> Yahoo-Simulation")
        return
    o = _gate_submit(_gate_name(bot), body)
    if not o or not o.get("id"):
        grund = (o or {}).get("reason") or (o or {}).get("gate") or "kein Versand"
        t.setdefault("log", []).append(f"Alpaca: Order nicht platziert ({grund}) -> Yahoo-Simulation")
        return
    t["alpaca"] = {"orderId": o["id"], "qty": qty}
    t.setdefault("log", []).append(f"Alpaca: Bracket-Order platziert ({qty} Stk.)")
    print(f"{t['id']} {t['ticker']}: Bracket {qty} Stk.")


def order_sync(keys, t, bot):
    risiko_usd = bot["risiko_usd"]
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
                eo = _gate_submit(_gate_name(bot), {
                    "symbol": t["ticker"], "qty": str(t["alpaca"]["qty"]),
                    "side": seite, "type": "market", "time_in_force": "opg"}) if _gate_submit else None
                if eo and eo.get("id"):
                    t["exitOrderId"] = eo["id"]
                    t.setdefault("log", []).append("Haltedauer erreicht -> MOO-Exit platziert")
                else:
                    t.setdefault("log", []).append(
                        f"MOO-Exit nicht platziert ({(eo or {}).get('reason', 'Gate?')}) -> naechster Lauf")
    if t["status"] in ("gewonnen", "verloren", "zeit_exit") and "ergebnisR" not in t:
        t["ergebnisR"] = r_multiple(t, t["exitKurs"])
        if bot.get("sizing") == "position":
            richtung = 1 if t["richtung"] == "long" else -1
            basis = t.get("entryFill", t["entry"])
            t["pnlEur"] = round(t["alpaca"]["qty"] * (t["exitKurs"] - basis) * richtung, 2)
        else:
            t["pnlEur"] = round(t["ergebnisR"] * risiko_usd, 2)


def main():
    for bot in BOTS:
        keys = keys_from_env(bot["prefix"])
        if not keys:
            print(f"{bot['journal']}: keine Keys - uebersprungen.")
            continue
        with open(bot["journal"], encoding="utf-8") as f:
            d = json.load(f)
        vorher = json.dumps(d, sort_keys=True)
        d.setdefault("konto", {})["alpaca"] = True
        d["konto"]["status"] = f"ALPACA PAPER ({bot['prefix']})"
        for t in d["trades"]:
            if "." in t.get("yahooSymbol", t["ticker"]):
                continue
            try:
                if t["status"] == "wartet" and "alpaca" not in t:
                    order_anlegen(keys, t, bot)
                if "alpaca" in t and t["status"] in ("wartet", "offen"):
                    order_sync(keys, t, bot)
            except RuntimeError as e:
                print(f"{t['id']}: {e}")
        d["statistik"] = statistik_neu(d["trades"])
        if json.dumps(d, sort_keys=True) != vorher:
            try:
                from atomwrite import write_atomic as _wa
                _wa(bot["journal"], json.dumps(d, ensure_ascii=False, indent=2) + "\n")
            except Exception:
                with open(bot["journal"], "w", encoding="utf-8") as f:
                    json.dump(d, f, ensure_ascii=False, indent=2)
                    f.write("\n")
            print(bot["journal"], "aktualisiert (Alpaca).")
        else:
            print(bot["journal"], "unveraendert (Alpaca).")


if __name__ == "__main__":
    main()
