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

    raw_body = request.data.decode("utf-8")
    print("RAW BODY:", raw_body)

    try:
        data = json.loads(raw_body)
    except Exception as e:
        print("JSON parse error:", e)
        return jsonify({"error": "Invalid JSON"}), 400

    print("PARSED JSON:", data)

    incoming_secret = str(data.get("secret", "")).strip()
    env_secret = str(TV_SECRET).strip()

    print("Incoming secret:", incoming_secret)
    print("Env secret:", env_secret)

    # Secret validation
    if env_secret and incoming_secret != env_secret:
        print("❌ SECRET MISMATCH")
        return jsonify({"error": "Unauthorized"}), 401

    print("✅ Secret OK")

    symbol = data.get("symbol", "N/A")
    tf = data.get("tf", "N/A")
    price = data.get("price", "N/A")
    time = data.get("time", "N/A")

    # Build simple Telegram message
    msg = (
        "🟢 TradingView Alert\n\n"
        f"Symbol: {symbol}\n"
        f"TF: {tf}\n"
        f"Price: {price}\n"
        f"Time: {time}"
    )

    ok = send_telegram(msg)

    return jsonify({"ok": ok}), (200 if ok else 500)


# ------------------------
# Manual Render test
# ------------------------
@app.route("/tg_test", methods=["GET"])
def tg_test():
    ok = send_telegram("✅ Render → Telegram connection OK")
    return jsonify({"ok": ok})
