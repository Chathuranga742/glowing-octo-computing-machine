import os
import time
import threading
import requests
from flask import Flask, request
import websocket
import json

app = Flask(__name__)

# Telegram Config (ඔයාගේ ටෝකන් සහ චැට් අයිඩී මෙතනට වැටෙයි - කලින් කෝඩ් එකේ තිබුණු ඒවාම දාන්න)
TELEGRAM_BOT_TOKEN = os.environ.get("8609436988:AAEEcnQgqZtlWPcOvMHgJGPhK8pTAz-TBeQ", "5573340878")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram Error: {e}")

# Deriv Volatility Indices 10
ASSETS = {
    "R_10": "Volatility 10 Index",
    "R_25": "Volatility 25 Index",
    "R_50": "Volatility 50 Index",
    "R_75": "Volatility 75 Index",
    "R_100": "Volatility 100 Index",
    "1HZ10V": "Volatility 10 (1s) Index",
    "1HZ25V": "Volatility 25 (1s) Index",
    "1HZ50V": "Volatility 50 (1s) Index",
    "1HZ75V": "Volatility 75 (1s) Index",
    "1HZ100V": "Volatility 100 (1s) Index"
}

latest_candles = {}

def on_message(ws, message):
    try:
        data = json.loads(message)
        if "ohlc" in data:
            candle = data["ohlc"]
            symbol = candle["symbol"]
            # Close price gannawa (Green nam o, < c, Red nam o > c)
            open_p = float(candle.get("open", 0))
            close_p = float(candle.get("close", 0))
            
            color = "🟢" if close_p >= open_p else "🔴"
            
            if symbol not in latest_candles:
                latest_candles[symbol] = []
                
            # Last candles list eke save karagannawa
            latest_candles[symbol].append(color)
            if len(latest_candles[symbol]) > 5:
                latest_candles[symbol].pop(0)
                
            # Pattern check karanawa (🔴🔴🟢 or 🟢🟢🔴)
            history = latest_candles[symbol]
            if len(history) >= 3:
                p1, p2, p3 = history[-3], history[-2], history[-1]
                if (p1 == "🔴" and p2 == "🔴" and p3 == "🟢") or (p1 == "🟢" and p2 == "🟢" and p3 == "🔴"):
                    signal_type = "📈 BUY (CALL)" if p3 == "🟢" else "📉 SELL (PUT)"
                    msg = f"🚨 *Deriv Reversal Signal!* 🚨\n\nAsset: `{ASSETS.get(symbol, symbol)}`\nPattern: `{p1} {p2} {p3}`\nAction: *{signal_type}*"
                    send_telegram_message(msg)
    except Exception as e:
        print(f"WS Error: {e}")

def on_error(ws, error):
    print(f"WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket Closed. Reconnecting...")
    time.sleep(5)
    start_websocket()

def on_open(ws):
    print("Connected to Deriv WebSocket! Subscribing to assets...")
    for symbol in ASSETS.keys():
        sub_req = {"sub_ticks_history": symbol, "style": "candles", "granularity": 60}
        ws.send(json.dumps(sub_req))

def start_websocket():
    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://ws.derivws.com/websockets/v3?app_id=1089",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever()
        except Exception as e:
            print(f"WS Loop Error: {e}")
            time.sleep(5)

@app.route("/", methods=["GET"])
def home():
    return "Deriv Bot is Running 24/7!", 200

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = request.get_json()
    if "message" in update:
        chat_id = update["message"]["chat_id"] if "chat_id" in update["message"] else update["message"]["chat"]["id"]
        text = update["message"].get("text", "")
        
        if text == "/test":
            send_telegram_message("✅ Bot is active and connected to Render successfully!")
        elif text == "/signal":
            # Manual request ekakata current status eka balanna
            status_msg = "📊 *Current Market Status Check:*\n"
            if not latest_candles:
                status_msg += "⏳ Data loading... Please wait a few seconds and try again."
            else:
                for sym, cols in latest_candles.items():
                    status_msg += f"- `{ASSETS.get(sym, sym)}`: `{' '.join(cols)}`\n"
            send_telegram_message(status_msg)
            
    return "OK", 200

if __name__ == "__main__":
    # Background thread eke Deriv WebSocket eka run karanawa
    ws_thread = threading.Thread(target=start_websocket, daemon=True)
    ws_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
