import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TV_SECRET = os.getenv("TRADINGVIEW_SECRET", "")


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


@app.route("/")
def home():
    return "OK"


@app.route("/tv", methods=["POST"])
def tv():

    raw_body = request.data.decode("utf-8", errors="ignore")

    print("========== WEBHOOK RECEIVED ==========")
    print(raw_body)
    print("======================================")

    # Simple secret check (string match, not JSON)
    if TV_SECRET and TV_SECRET not in raw_body:
        print("❌ Secret NOT found in payload")
        return jsonify({"error": "Unauthorized"}), 401

    # Send RAW message straight to Telegram
    msg = "📡 TradingView Alert\n\n" + raw_body

    ok = send_telegram(msg)

    return jsonify({"ok": ok}), 200
