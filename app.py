import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TV_SECRET = os.getenv("TRADINGVIEW_SECRET", "")


# -------------------
# Telegram sender
# -------------------
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    r = requests.post(
        url,
        json={
            "chat_id": TG_CHAT_ID,
            "text": text
        },
        timeout=15
    )

    print("Telegram status:", r.status_code)
    print("Telegram response:", r.text)

    return r.status_code == 200


# -------------------
# Health check
# -------------------
@app.route("/", methods=["GET"])
def home():
    return "OK"


# -------------------
# TradingView webhook
# -------------------
@app.route("/tv", methods=["POST"])
def tv():

    print("\n=== WEBHOOK RECEIVED ===")

    # TradingView sends text/plain so we must parse manually
    raw_body = request.data.decode("utf-8", errors="ignore")

    print("Raw body:", raw_body)

    try:
        data = json.loads(raw_body)
    except Exception as e:
        print("JSON parse failed:", str(e))
        send_telegram("❌ Webhook received but JSON parse failed.")
        return jsonify({"error": "Invalid JSON"}), 400


    # -------------------
    # Secret validation
    # -------------------
    incoming_secret = str(data.get("secret", "")).strip()
    env_secret = str(TV_SECRET).strip()

    if env_secret and incoming_secret != env_secret:
        print("SECRET MISMATCH", incoming_secret, env_secret)
        send_telegram("❌ Secret mismatch from TradingView webhook.")
        return jsonify({"error": "Unauthorized"}), 401


    # -------------------
    # Extract fields
    # -------------------
    symbol = data.get("symbol", "N/A")
    tf = data.get("tf", "N/A")
    price = data.get("price", "N/A")
    time_val = data.get("time", "N/A")
    msg = data.get("message", "")

    print("Symbol:", symbol)
    print("TF:", tf)
    print("Price:", price)
    print("Time:", time_val)


    # -------------------
    # Build Telegram message
    # -------------------
    text = (
        "📡 TradingView Alert\n\n"
        f"Symbol: {symbol}\n"
        f"TF: {tf}\n"
        f"Price: {price}\n"
        f"Time: {time_val}\n\n"
        f"{msg}"
    )


    ok = send_telegram(text)

    return jsonify({"ok": ok}), (200 if ok else 500)
