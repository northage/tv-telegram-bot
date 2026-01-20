import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TG_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN", "") or "").strip()
TG_CHAT_ID = (os.getenv("TELEGRAM_CHAT_ID", "") or "").strip()
TV_SECRET = (os.getenv("TRADINGVIEW_SECRET", "") or "").strip()

def tg_send(text: str, parse_mode: str | None = None) -> tuple[bool, str]:
    """Send message to Telegram. Returns (ok, response_text)."""
    if not TG_TOKEN or not TG_CHAT_ID:
        return False, "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID env var"

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        r = requests.post(url, json=payload, timeout=20)
        return (r.status_code == 200), r.text
    except Exception as e:
        return False, f"Telegram request error: {e}"

def parse_tradingview_payload():
    """
    TradingView often POSTs with Content-Type text/plain even when body is JSON.
    So:
      - try request.get_json()
      - else try json.loads(raw body)
      - else treat raw body as plain text
    Returns: (data_dict, raw_text)
    """
    raw = (request.get_data(as_text=True) or "").strip()

    data = request.get_json(silent=True)
    if isinstance(data, dict) and data:
        return data, raw

    # If get_json fails (common), try parsing raw as JSON
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed, raw
        except Exception:
            pass

    # Nothing parseable
    return {}, raw

@app.route("/", methods=["GET"])
def home():
    return "OK", 200

# Quick Render -> Telegram test (no TradingView needed)
@app.route("/tg_test", methods=["GET"])
def tg_test():
    ok, resp = tg_send("✅ Render → Telegram test message")
    return jsonify({"ok": ok, "telegram_response": resp}), (200 if ok else 500)

@app.route("/tv", methods=["POST"])
def tv():
    data, raw = parse_tradingview_payload()

    print("---- Incoming /tv ----")
    print("Content-Type:", request.headers.get("Content-Type"))
    print("Raw body:", raw[:2000])  # cap log size
    print("Parsed dict:", data)

    # Secret check ONLY if env secret is set
    if TV_SECRET:
        incoming_secret = (data.get("secret") or "").strip()
        if incoming_secret != TV_SECRET:
            print("❌ Secret mismatch", {"incoming": incoming_secret, "env": TV_SECRET})
            return jsonify({"error": "Unauthorized"}), 401

    # If body isn't JSON but plain text, forward it
    if not data and raw:
        ok, resp = tg_send(f"TradingView Alert (raw):\n{raw}")
        print("Telegram:", ok, resp)
        return jsonify({"ok": ok, "telegram_response": resp}), (200 if ok else 500)

    # Normal JSON path
    typ = data.get("type", "UNKNOWN")
    symbol = data.get("symbol", "N/A")
    tf = data.get("tf", "N/A")
    price = data.get("price", "N/A")
    t = data.get("time", "N/A")

    # Prefer message/text if provided (your Pine sends message)
    msg = data.get("message") or data.get("text")
    if not msg:
        # fallback: build simple message from fields
        msg = (
            f"🧪 TradingView Alert\n"
            f"Type: {typ}\n"
            f"Symbol: {symbol}\n"
            f"TF: {tf}\n"
            f"Price: {price}\n"
            f"Time: {t}"
        )

    ok, resp = tg_send(msg)
    print("Telegram:", ok, resp)
    return jsonify({"ok": ok, "telegram_response": resp}), (200 if ok else 500)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
