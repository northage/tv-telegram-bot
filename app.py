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

@app.route("/tv", methods=["POST"])
def tv():
    data = request.json

    if data.get("secret") != TV_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    message = data.get("message", "TradingView Alert")
    send_telegram(message)

    return jsonify({"status": "sent"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
