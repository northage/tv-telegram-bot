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

    if data.get("secret") != TV_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    typ = data.get("type", "UNKNOWN")
    symbol = data.get("symbol", "N/A")
    tf = data.get("tf", "N/A")

    # scheduled zones message
    if typ == "SCHEDULED_ZONES":
        slot = data.get("slot_gmt", "N/A")
        t = fmt_time_from_ms(data.get("time_ms"))

        vwap = fmt_price(data.get("vwap"))

        buy = data.get("buy", {}) or {}
        sell = data.get("sell", {}) or {}

        text = (
            f"📊 *Scheduled VWAP Deviation Zones*\n"
            f"*Symbol:* {symbol}\n"
            f"*Timeframe:* {tf}\n"
            f"*Schedule (GMT):* {slot}\n"
            f"*Bar Close:* {t}\n\n"
            f"🟩 *BUY Zones (Dev2–Dev5)*\n"
            f"• Dev2: {fmt_price(buy.get('dev2'))}\n"
            f"• Dev3: {fmt_price(buy.get('dev3'))}\n"
            f"• Dev4: {fmt_price(buy.get('dev4'))}\n"
            f"• Dev5: {fmt_price(buy.get('dev5'))}\n"
            f"• SL:  {fmt_price(buy.get('sl'))}  _( $2 beyond Dev5 )_\n"
            f"• TP:  {fmt_price(buy.get('tp'))}  _(VWAP)_\n\n"
            f"🟥 *SELL Zones (Dev2–Dev5)*\n"
            f"• Dev2: {fmt_price(sell.get('dev2'))}\n"
            f"• Dev3: {fmt_price(sell.get('dev3'))}\n"
            f"• Dev4: {fmt_price(sell.get('dev4'))}\n"
            f"• Dev5: {fmt_price(sell.get('dev5'))}\n"
            f"• SL:  {fmt_price(sell.get('sl'))}  _( $2 beyond Dev5 )_\n"
            f"• TP:  {fmt_price(sell.get('tp'))}  _(VWAP)_\n\n"
            f"⚠️ *Note:* Zones are reference levels, not trade advice."
        )

        # IMPORTANT: enable Markdown
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"})
        return jsonify({"ok": True}), 200

    # fallback (other alert types)
    message = data.get("message") or f"TradingView Alert ({typ})"
    send_telegram(message)
    return jsonify({"ok": True}), 200
