# -*- coding: utf-8 -*-
"""Small Alpaca Trading API helper shared by the bot scripts.

Only reads credentials from environment variables. No local key files.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import urllib.error
import urllib.request


BASE_URL = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets/v2").rstrip("/")
OPEN_STATUSES = {"new", "accepted", "pending_new", "partially_filled", "held", "accepted_for_bidding"}
DONE_STATUSES = {"filled", "canceled", "expired", "rejected", "done_for_day"}


def keys_from_env(prefix: str) -> tuple[str, str] | None:
    key = os.environ.get(prefix + "_KEY", "").strip()
    secret = os.environ.get(prefix + "_SECRET", "").strip()
    if not key or not secret:
        return None
    return key, secret


def api(keys: tuple[str, str], path: str, method: str = "GET", body: dict | None = None) -> dict:
    req = urllib.request.Request(
        BASE_URL + path,
        method=method,
        headers={
            "APCA-API-KEY-ID": keys[0],
            "APCA-API-SECRET-KEY": keys[1],
            "Content-Type": "application/json",
        },
        data=json.dumps(body).encode() if body is not None else None,
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            content = response.read().decode()
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as exc:
        message = exc.read().decode(errors="replace")[:300]
        raise RuntimeError(f"{method} {path}: HTTP {exc.code} {message}") from exc


def price(value: float) -> str:
    places = 4 if abs(value) < 1 else 2
    return f"{float(value):.{places}f}"


def qty_for_risk(entry: float, stop: float, risk_usd: float) -> int:
    risk = abs(float(entry) - float(stop))
    if risk <= 0:
        return 0
    return math.floor(float(risk_usd) / risk)


def iso_to_date(value: str | None) -> str | None:
    if not value:
        return None
    return value[:10]


def iso_to_utc_hhmm(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value[11:16] if len(value) >= 16 else value
    return parsed.astimezone(dt.UTC).strftime("%H:%M")


def ny_now() -> dt.datetime:
    try:
        from zoneinfo import ZoneInfo

        return dt.datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        return dt.datetime.utcnow().replace(tzinfo=dt.UTC) - dt.timedelta(hours=5)
