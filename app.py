import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TG_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
TG_CHAT_ID = (os.getenv("TELEGRAM_CHAT_ID") or "").strip()
TV_SECRET = (os.getenv("TRADINGVIEW_SECRET") or "").strip()

TELEGRAM_API = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"


def telegram_send(text: str) -> tuple[bool, int, str]:
    """Send a plain text Telegram message. Returns (ok, status_code, response_text)."""
    if not TG_TOKEN or not TG_CHAT_ID:
        return False, 0, "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"

    try:
        r = requests.post(
            TELEGRAM_API,
            json={"chat_id": TG_CHAT_ID, "text": text},
            timeout=20,
        )
        return (r.status_code == 200), r.status_code, r.text
    except Exception as e:
        return False, 0, f"Exception: {e}"


@app.get("/")
def home():
    return "OK", 200


@app.get("/tg_test")
def tg_test():
    ok, code, resp = telegram_send("✅ Render → Telegram test message")
    return jsonify({"ok": ok, "status": code, "telegram_response": resp}), (200 if ok else 500)


@app.post("/tv")
def tv():
    # Log raw request so we can diagnose content-type / body issues
    raw = request.get_data(as_text=True) or ""
    print("==== /tv HIT ====")
    print("Content-Type:", request.headers.get("Content-Type"))
    print("Raw body:", raw[:2000])

    data = request.get_json(silent=True) or {}
    print("Parsed JSON:", data)

    # Optional secret check (ONLY enforce if env secret exists)
    incoming_secret = (data.get("secret") or "").strip()
    if TV_SECRET and incoming_secret != TV_SECRET:
        print("❌ Secret mismatch:", {"incoming": incoming_secret, "env": TV_SECRET})
        return jsonify({"ok": False, "error": "Unauthorized (secret mismatch)"}), 401

    # Build a SIMPLE message (price + time) no matter what type arrives
    typ = data.get("type", "TV_ALERT")
    symbol = data.get("symbol") or data.get("ticker") or "XAUUSD"
    tf = data.get("tf") or data.get("timeframe") or "N/A"
    price = data.get("price") or data.get("close") or "N/A"
    t = data.get("time") or data.get("timeStr") or data.get("time_gmt") or "N/A"

    # If Pine sends a prebuilt message/text, prefer it
    prebuilt = data.get("message") or data.get("text")

    if prebuilt:
        message = str(prebuilt)
    else:
        message = (
            f"TradingView Alert\n"
            f"Type: {typ}\n"
            f"Symbol: {symbol}\n"
            f"TF: {tf}\n"
            f"Price: {price}\n"
            f"Time: {t}"
        )

    ok, code, resp = telegram_send(message)
    print("Telegram send:", {"ok": ok, "status": code, "resp": resp[:500]})

    return jsonify(
        {
            "ok": ok,
            "telegram_status": code,
            "telegram_response": resp,
            "received": data,
        }
    ), (200 if ok else 500)


if __name__ == "__main__":
    # Local dev only; Render uses gunicorn
    app.run(host="0.0.0.0", port=10000)
