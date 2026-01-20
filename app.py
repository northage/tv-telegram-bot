import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TV_SECRET = os.getenv("TRADINGVIEW_SECRET", "")

# ------------------------
# Telegram sender
# ------------------------
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": TG_CHAT_ID,
        "text": text
    }, timeout=15)

    print("Telegram status:", r.status_code)
    print("Telegram response:", r.text)

    return r.status_code == 200


# ------------------------
# Health check
# ------------------------
@app.route("/", methods=["GET"])
def home():
    return "OK"


# ------------------------
# TradingView webhook
# ------------------------
@app.route("/tv", methods=["POST"])
def tv():
    raw_body = request.data.decode("utf-8", errors="replace")
    print("RAW BODY:", raw_body)

    data = {}
    try:
        data = json.loads(raw_body)
        print("PARSED JSON:", data)
    except Exception as e:
        print("JSON parse failed:", e)

    # If JSON parsed, enforce secret
    env_secret = (TV_SECRET or "").strip()
    incoming_secret = (str(data.get("secret", "")) if data else "").strip()

    if env_secret:
        # If we couldn't parse JSON, we can't verify secret -> reject
        if not data or incoming_secret != env_secret:
            print("❌ SECRET MISMATCH", {"incoming": incoming_secret, "env": env_secret})
            return jsonify({"error": "Unauthorized"}), 401

    # Build message
    if data:
        symbol = data.get("symbol", "N/A")
        tf = data.get("tf", "N/A")
        price = data.get("price", "N/A")
        t = data.get("time", "N/A")
        msg = f"🟢 TradingView Alert\n\nSymbol: {symbol}\nTF: {tf}\nPrice: {price}\nTime: {t}"
    else:
        # Fallback: forward raw body
        msg = f"🟠 TradingView Raw Alert:\n{raw_body}"

    ok = send_telegram(msg)
    return jsonify({"ok": ok}), (200 if ok else 500)



# ------------------------
# Manual Render test
# ------------------------
@app.route("/tg_test", methods=["GET"])
def tg_test():
    ok = send_telegram("✅ Render → Telegram connection OK")
    return jsonify({"ok": ok})
