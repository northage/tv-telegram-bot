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
    data = request.get_json()

    if not data:
        send_telegram("❌ Empty TradingView payload")
        return jsonify({"error": "no data"}), 400

    if data.get("secret") != TV_SECRET:
        send_telegram("❌ Wrong TradingView secret")
        return jsonify({"error": "Unauthorized"}), 401

    symbol = data.get("symbol", "N/A")
    tf     = data.get("tf", "N/A")
    price  = data.get("price", "N/A")
    t      = data.get("time", "N/A")
    typ    = data.get("type", "SIGNAL")

    msg = (
        f"🚨 TradingView Signal\n\n"
        f"Type: {typ}\n"
        f"Symbol: {symbol}\n"
        f"TF: {tf}\n"
        f"Price: {price}\n"
        f"Time: {t}"
    )

    send_telegram(msg)
    return jsonify({"ok": True}), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
