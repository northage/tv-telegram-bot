import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TG_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
TV_SECRET  = os.getenv("TRADINGVIEW_SECRET", "").strip()


def tg_send(text: str) -> tuple[bool, str]:
    if not TG_TOKEN or not TG_CHAT_ID:
        return False, "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    r = requests.post(
        url,
        json={"chat_id": TG_CHAT_ID, "text": text},
        timeout=20
    )
    return (r.status_code == 200), f"{r.status_code} {r.text}"


@app.route("/", methods=["GET"])
def home():
    return "OK"


# Quick Render -> Telegram check
@app.route("/tg_test", methods=["GET"])
def tg_test():
    ok, info = tg_send("✅ Render → Telegram connection OK")
    return jsonify({"ok": ok, "info": info}), (200 if ok else 500)


@app.route("/tv", methods=["POST"])
def tv():
    raw = request.get_data(as_text=True) or ""
    print("=== WEBHOOK RECEIVED ===")
    print("Content-Type:", request.headers.get("Content-Type"))
    print("Raw body:", raw[:2000])

    # 1) Parse JSON safely (TradingView sometimes sends text/plain)
    data = {}
    try:
        data = request.get_json(silent=True) or {}
        if not data and raw.strip().startswith("{"):
            data = json.loads(raw)
    except Exception as e:
        print("JSON parse failed:", str(e))
        tg_send("❌ Webhook received but JSON parse failed.\n\n" + raw[:1500])
        return jsonify({"error": "bad json"}), 400

    print("Parsed keys:", list(data.keys()))

    # 2) Secret check (only if env secret set)
    incoming_secret = (data.get("secret") or "").strip()
    if TV_SECRET and incoming_secret != TV_SECRET:
        print("❌ SECRET MISMATCH", {"incoming": incoming_secret, "env": TV_SECRET})
        tg_send("❌ Secret mismatch — webhook blocked.")
        return jsonify({"error": "unauthorized"}), 401

    # 3) Build final Telegram message (ONLY the message/text field)
    typ = data.get("type", "UNKNOWN")
    symbol = data.get("symbol", "N/A")
    tf = data.get("tf", "N/A")
    price = data.get("price", "N/A")
    t = data.get("time", "N/A")

    msg = (data.get("message") or "").strip()
    if not msg:
        msg = (data.get("text") or "").strip()

    # If Pine didn’t include a message, create one:
    if not msg:
        msg = (
            f"📣 TradingView Alert\n"
            f"Type: {typ}\n"
            f"Symbol: {symbol}\n"
            f"TF: {tf}\n"
            f"Price: {price}\n"
            f"Time: {t}"
        )

    # 4) Send to Telegram
    ok, info = tg_send(msg)
    print("Telegram send:", ok, info)

    return jsonify({"ok": ok, "info": info}), (200 if ok else 500)
