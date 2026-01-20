import os
from datetime import datetime, timezone
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- ENV (Render) ---
TG_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
TG_CHAT_ID = (os.getenv("TELEGRAM_CHAT_ID") or "").strip()
TV_SECRET = (os.getenv("TRADINGVIEW_SECRET") or "").strip()


# ------------------------------
# Helpers
# ------------------------------
def _log(*args):
    # Render shows stdout in Logs
    print(*args, flush=True)


def fmt_price(x):
    try:
        return f"{float(x):,.2f}"
    except Exception:
        return "N/A"


def fmt_time_from_ms(ms):
    try:
        dt = datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return "N/A"


def send_telegram(text: str, parse_mode: str | None = None) -> tuple[bool, int, str]:
    """
    Sends a Telegram message and returns (ok, status_code, response_text)
    """
    if not TG_TOKEN:
        return False, 0, "Missing TELEGRAM_BOT_TOKEN"
    if not TG_CHAT_ID:
        return False, 0, "Missing TELEGRAM_CHAT_ID"

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}

    # Only set parse_mode when requested (Markdown can fail if text has bad chars)
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        r = requests.post(url, json=payload, timeout=20)
        return (r.status_code == 200), r.status_code, r.text
    except Exception as e:
        return False, 0, f"Telegram exception: {repr(e)}"


# ------------------------------
# Routes
# ------------------------------
@app.route("/", methods=["GET"])
def home():
    return "OK"


@app.route("/tg_test", methods=["GET"])
def tg_test():
    """
    Quick Render -> Telegram test. Visit:
    https://YOUR-RENDER-URL/tg_test
    """
    ok, status, body = send_telegram("✅ Render → Telegram test message")
    _log("TG_TEST:", {"ok": ok, "status": status, "body": body})
    return jsonify({"ok": ok, "status": status, "body": body}), (200 if ok else 500)


@app.route("/tv", methods=["POST"])
def tv():
    # --- Log raw request (this is the best debugging tool) ---
    _log("---- /tv HIT ----")
    _log("Headers:", dict(request.headers))
    raw = request.get_data(as_text=True)
    _log("Raw body:", raw)

    data = request.get_json(silent=True) or {}
    _log("Parsed JSON:", data)

    # --- Secret check (only enforced if TRADINGVIEW_SECRET is set) ---
    incoming_secret = (data.get("secret") or "").strip()
    if TV_SECRET and incoming_secret != TV_SECRET:
        _log("SECRET MISMATCH:", {"incoming": incoming_secret, "env": TV_SECRET})
        return jsonify({"error": "Unauthorized"}), 401

    typ = data.get("type", "UNKNOWN")
    symbol = data.get("symbol", "N/A")
    tf = data.get("tf", "N/A")

    # ------------------------------
    # SCHEDULED_ZONES formatting
    # ------------------------------
    if typ == "SCHEDULED_ZONES":
        slot = data.get("slot_gmt", "N/A")

        # Your Pine currently sends "time" as a string like: "2026-01-20 17:08 UTC"
        # If you later send time_ms, we support that too.
        t = data.get("time") or fmt_time_from_ms(data.get("time_ms"))

        vwap = fmt_price(data.get("vwap"))
        buy = data.get("buy", {}) or {}
        sell = data.get("sell", {}) or {}

        # Keep it plain text (no Markdown) to avoid parse errors while testing.
        text = (
            "📊 Scheduled VWAP Deviation Zones\n"
            f"Symbol: {symbol}\n"
            f"Timeframe: {tf}\n"
            f"Slot (GMT): {slot}\n"
            f"Bar Close: {t}\n"
            f"VWAP: {vwap}\n\n"
            "🟩 BUY (Dev2–Dev5)\n"
            f"Dev2: {fmt_price(buy.get('dev2'))}\n"
            f"Dev3: {fmt_price(buy.get('dev3'))}\n"
            f"Dev4: {fmt_price(buy.get('dev4'))}\n"
            f"Dev5: {fmt_price(buy.get('dev5'))}\n"
            f"SL:   {fmt_price(buy.get('sl'))}\n"
            f"TP:   {fmt_price(buy.get('tp'))}\n\n"
            "🟥 SELL (Dev2–Dev5)\n"
            f"Dev2: {fmt_price(sell.get('dev2'))}\n"
            f"Dev3: {fmt_price(sell.get('dev3'))}\n"
            f"Dev4: {fmt_price(sell.get('dev4'))}\n"
            f"Dev5: {fmt_price(sell.get('dev5'))}\n"
            f"SL:   {fmt_price(sell.get('sl'))}\n"
            f"TP:   {fmt_price(sell.get('tp'))}\n"
        )

        ok, status, body = send_telegram(text)
        _log("Telegram send (SCHEDULED_ZONES):", {"ok": ok, "status": status, "body": body})
        return jsonify({"ok": ok, "telegram_status": status, "telegram_body": body}), (200 if ok else 500)

    # ------------------------------
    # Fallback / TV_TEST etc.
    # ------------------------------
    message = data.get("message") or data.get("text") or f"TradingView Alert ({typ})"
    ok, status, body = send_telegram(message)
    _log("Telegram send (fallback):", {"ok": ok, "status": status, "body": body})
    return jsonify({"ok": ok, "telegram_status": status, "telegram_body": body}), (200 if ok else 500)


# Optional: local run
if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
