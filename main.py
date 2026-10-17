import asyncio
import json
import os
import threading
import requests
import websockets
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

# Telegram /test Command Listener
def poll_telegram_commands():
    last_update_id = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=5"
            res = requests.get(url, timeout=10).json()
            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    text = msg.get("text", "")
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    
                    if text == "/test" and chat_id == TELEGRAM_CHAT_ID:
                        send_telegram_msg("✅ *BOT IS LIVE & SCALPING DERIV 24/7!*\n\n📊 Volatility Indices 10 ම Scan වෙමින් පවතී. Pattern එකක් ලැබුණු සැනින් Signals එනු ඇත! 🚀")
        except Exception as e:
            pass
        threading.Event().wait(3)

@app.route('/')
def home():
    return "Deriv Fast Signal Engine is Active 24/7!"

async def monitor_symbol(symbol):
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    while True:
        try:
            async with websockets.connect(uri, extra_headers=headers) as websocket:
                req = {
                    "ticks_history": symbol,
                    "adjust_start_time": 1,
                    "count": 10,
                    "end": "latest",
                    "style": "candles",
                    "granularity": 60,
                    "subscribe": 1
                }
                await websocket.send(json.dumps(req))
                
                candles_list = []
                last_epoch = 0
                
                while True:
                    res = json.loads(await websocket.recv())
                    
                    if "candles" in res:
                        candles_list = res["candles"]
                        
                    elif "ohlc" in res:
                        ohlc = res["ohlc"]
                        current_epoch = ohlc["open_time"]
                        
                        if current_epoch != last_epoch and len(candles_list) >= 3:
                            c1 = candles_list[-3]
                            c2 = candles_list[-2]
                            c3 = candles_list[-1]
                            
                            c1_g = c1["close"] > c1["open"]
                            c2_g = c2["close"] > c2["open"]
                            c3_r = c3["close"] < c3["open"]
                            
                            c1_r = c1["close"] < c1["open"]
                            c2_r = c2["close"] < c2["open"]
                            c3_g = c3["close"] > c3["open"]
                            
                            # Pattern 1: 🔴🔴 ➔ 🟢 (BUY Signal)
                            if c1_r and c2_r and c3_g:
                                min_low = min(c1["low"], c2["low"])
                                send_telegram_msg(
                                    f"🟢 *FAST BUY SIGNAL*\n\n"
                                    f"📊 *Market:* {symbol}\n"
                                    f"🕯️ *Pattern:* 🔴🔴🟢 (2 Red + 1 Green)\n"
                                    f"🎯 *Support Level:* {min_low}\n"
                                    f"⚡ *Action:* Open HIGHER Trade Now!"
                                )
                                
                            # Pattern 2: 🟢🟢 ➔ 🔴 (SELL Signal)
                            elif c1_g and c2_g and c3_r:
                                max_high = max(c1["high"], c2["high"])
                                send_telegram_msg(
                                    f"🔴 *FAST SELL SIGNAL*\n\n"
                                    f"📊 *Market:* {symbol}\n"
                                    f"🕯️ *Pattern:* 🟢🟢🔴 (2 Green + 1 Red)\n"
                                    f"🎯 *Resistance Level:* {max_high}\n"
                                    f"⚡ *Action:* Open LOWER Trade Now!"
                                )
                                
                            last_epoch = current_epoch
                            
                            candles_list.append({
                                "open": float(ohlc["open"]),
                                "high": float(ohlc["high"]),
                                "low": float(ohlc["low"]),
                                "close": float(ohlc["close"]),
                                "epoch": ohlc["open_time"]
                            })
                            if len(candles_list) > 20:
                                candles_list.pop(0)

        except Exception as e:
            await asyncio.sleep(5)

async def start_all_monitors():
    send_telegram_msg("🚀 *Deriv Signal Bot Online! Type /test to check live status.*")
    tasks = [monitor_symbol(sym) for sym in SYMBOLS]
    await asyncio.gather(*tasks)

def run_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_all_monitors())

t_bot = threading.Thread(target=run_async_loop, daemon=True)
t_bot.start()

t_cmd = threading.Thread(target=poll_telegram_commands, daemon=True)
t_cmd.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
