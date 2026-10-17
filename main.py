import time
import os
import requests
import threading
from flask import Flask

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "8609436988:AAEEcnQgqZtlWPcOvMHgJGPhK8pTAz-TBeQ"
TELEGRAM_CHAT_ID = "5573340878"

SYMBOLS = [
    "R_10", "R_25", "R_50", "R_75", "R_100",
    "1HZ10V", "1HZ25V", "1HZ50V", "1HZ75V", "1HZ100V"
]

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(">>> Telegram Error:", e)

@app.route('/')
def home():
    return "Deriv Polling Engine Active 24/7!"

processed_epochs = {}

def check_deriv_markets():
    print(">>> Signal Engine Worker Started...")
    send_telegram_msg("🚀 *Deriv Signal Engine 3.0 (Ultra-Reliable) Online!*")
    
    while True:
        for symbol in SYMBOLS:
            try:
                # Deriv Direct REST Endpoint for Candle History
                url = f"https://api.deriv.com/api-v1/candles?symbol={symbol}&granularity=60&count=5"
                # Using Public Deriv API
                ws_url = "https://wss.derivws.com/websockets/v3?app_id=1089"
                
                # Fetch candle history directly via API
                payload = {
                    "ticks_history": symbol,
                    "adjust_start_time": 1,
                    "count": 5,
                    "end": "latest",
                    "style": "candles",
                    "granularity": 60
                }
                
                res = requests.post("https://api.deriv.com/api/v1/ticks_history", json=payload, timeout=5)
                # Fallback to direct HTTP request using Deriv HTTP API / WebSocket proxy if needed
            except Exception as e:
                pass

        time.sleep(10)

# Direct Lightweight Polling via Deriv WebSocket Request
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    if "candles" in data:
        candles = data["candles"]
        req_id = data.get("echo_req", {}).get("ticks_history", "")
        
        if len(candles) >= 3:
            c1 = candles[-3]
            c2 = candles[-2]
            c3 = candles[-1]
            
            epoch = c3["epoch"]
            if processed_epochs.get(req_id) != epoch:
                c1_r = c1["close"] < c1["open"]
                c2_r = c2["close"] < c2["open"]
                c3_g = c3["close"] > c3["open"]
                
                c1_g = c1["close"] > c1["open"]
                c2_g = c2["close"] > c2["open"]
                c3_r = c3["close"] < c3["open"]
                
                # 🔴🔴🟢 BUY Signal
                if c1_r and c2_r and c3_g:
                    min_low = min(c1["low"], c2["low"])
                    send_telegram_msg(
                        f"🟢 *FAST BUY SIGNAL*\n\n"
                        f"📊 *Market:* {req_id}\n"
                        f"🕯️ *Pattern:* 🔴🔴🟢 (2 Red + 1 Green)\n"
                        f"🎯 *Support Level:* {min_low}\n"
                        f"⚡ *Action:* Open HIGHER Trade Now!"
                    )
                    processed_epochs[req_id] = epoch
                    
                # 🟢🟢🔴 SELL Signal
                elif c1_g and c2_g and c3_r:
                    max_high = max(c1["high"], c2["high"])
                    send_telegram_msg(
                        f"🔴 *FAST SELL SIGNAL*\n\n"
                        f"📊 *Market:* {req_id}\n"
                        f"🕯️ *Pattern:* 🟢🟢🔴 (2 Green + 1 Red)\n"
                        f"🎯 *Resistance Level:* {max_high}\n"
                        f"⚡ *Action:* Open LOWER Trade Now!"
                    )
                    processed_epochs[req_id] = epoch

def run_polling_loop():
    send_telegram_msg("🚀 *Deriv Signal Engine 3.0 Activated!*")
    while True:
        try:
            ws = websocket.create_connection("wss://ws.derivws.com/websockets/v3?app_id=1089")
            for sym in SYMBOLS:
                req = {
                    "ticks_history": sym,
                    "adjust_start_time": 1,
                    "count": 5,
                    "end": "latest",
                    "style": "candles",
                    "granularity": 60
                }
                ws.send(json.dumps(req))
                res = ws.recv()
                on_message(ws, res)
            ws.close()
        except Exception as e:
            print(">>> Connection retry:", e)
        time.sleep(10)

t = threading.Thread(target=run_polling_loop, daemon=True)
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
