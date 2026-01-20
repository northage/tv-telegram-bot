import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TV_SECRET = os.getenv("TRADINGVIEW_SECRET", "")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text})
    return r.status_code == 200

@app.route("/", methods=["GET"])
def home():
    return "OK"
from datetime import datetime, timezone

from datetime import datetime, timezone

def fmt_price(x):
    try:
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"

def fmt_time_from_ms(ms):
    try:
        dt = datetime.fromtimestamp(int(ms)/1000, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return "N/A"

@app.route("/tv", methods=["POST"])
def tv():
    data = request.get_json(silent=True) or {}
    print("Incoming /tv:", data)

    # Secret check (only if env secret is set)
    env_secret = (TV_SECRET or "").strip()
    incoming_secret = (data.get("secret") or "").strip()

    if env_secret and incoming_secret != env_secret:
        print("Unauthorized: secret mismatch", {"incoming": incoming_secret, "env": env_secret})
        return jsonify({"error": "Unauthorized"}), 401

    typ = data.get("type", "UNKNOWN")
    symbol = data.get("symbol", "N/A")
    tf = data.get("tf", "N/A")

    # Scheduled zones message
    if typ == "SCHEDULED_ZONES":
        slot = data.get("slot_gmt", "N/A")

        # Your Pine payload sends time as a STRING like "2026-01-20 17:08 UTC"
        # So prefer 'time' directly, fallback to time_ms formatter if you later add it.
        t = data.get("time") or fmt_time_from_ms(data.get("time_ms"))

        buy = data.get("buy", {}) or {}
        sell = data.get("sell", {}) or {}

        text = (
            f"📊 Scheduled VWAP Deviation Zones\n"
            f"Symbol: {symbol}\n"
            f"Timeframe: {tf}\n"
            f"Slot (GMT): {slot}\n"
            f"Bar Close: {t}\n\n"
            f"BUY (Dev2–Dev5)\n"
            f"Dev2: {fmt_price(buy.get('dev2'))}\n"
            f"Dev3: {fmt_price(buy.get('dev3'))}\n"
            f"Dev4: {fmt_price(buy.get('dev4'))}\n"
            f"Dev5: {fmt_price(buy.get('dev5'))}\n"
            f"SL:   {fmt_price(buy.get('sl'))}  ($2 beyond Dev5)\n"
            f"TP:   {fmt_price(buy.get('tp'))}  (VWAP)\n\n"
            f"SELL (Dev2–Dev5)\n"
            f"Dev2: {fmt_price(sell.get('dev2'))}\n"
            f"Dev3: {fmt_price(sell.get('dev3'))}\n"
            f"Dev4: {fmt_price(sell.get('dev4'))}\n"
            f"Dev5: {fmt_price(sell.get('dev5'))}\n"
            f"SL:   {fmt_price(sell.get('sl'))}  ($2 beyond Dev5)\n"
            f"TP:   {fmt_price(sell.get('tp'))}  (VWAP)\n"
        )

        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text}, timeout=15)
        print("Telegram response:", r.status_code, r.text)
        return jsonify({"ok": r.status_code == 200}), (200 if r.status_code == 200 else 500)

    # Fallback (TV_TEST etc.)
    message = data.get("message") or data.get("text") or f"TradingView Alert ({typ})"
    ok = send_telegram(message)
    print("Telegram ok:", ok)
    return jsonify({"ok": ok}), (200 if ok else 500)
