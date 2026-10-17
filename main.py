import asyncio
import json
import os
import threading
import requests
import websockets
from flask import Flask

app = Flask(__name__)

# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN = "8609436988:AAEEcnQgqZtlWPcOvMHgJGPhK8pTAz-TBeQ"
TELEGRAM_CHAT_ID = "5573340878"

# Volatility Indices
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
    return "Deriv Precise Signal Bot is Active 24/7!"

async def monitor_symbol(symbol):
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    while True:
        try:
            async with websockets.connect(uri, extra_headers=headers) as websocket:
                req = {
                    "ticks_history": symbol,
                    "adjust_start_time": 1,
                    "count": 15,
                    "end": "latest",
                    "style": "candles",
                    "granularity": 60,
                    "subscribe": 1
                }
                await websocket.send(json.dumps(req))
                
                candles_list = []
                last_epoch = 0
                alerted_3_epoch = 0
                
                while True:
                    res = json.loads(await websocket.recv())
                    
                    if "candles" in res:
                        candles_list = res["candles"]
                        
                    elif "ohlc" in res:
                        ohlc = res["ohlc"]
                        current_epoch = ohlc["open_time"]
                        
                        # Candle එකක් සම්පූර්ණයෙන් Close වුණාම පමණක් Check කරයි
                        if current_epoch != last_epoch and len(candles_list) >= 4:
                            c1 = candles_list[-4] # Older candle
                            c2 = candles_list[-3]
                            c3 = candles_list[-2] # 3rd candle
                            c4 = candles_list[-1] # Newly closed candle
                            
                            c1_g = c1["close"] > c1["open"]
                            c2_g = c2["close"] > c2["open"]
                            c3_g = c3["close"] > c3["open"]
                            c4_r = c4["close"] < c4["open"]
                            
                            c1_r = c1["close"] < c1["open"]
                            c2_r = c2["close"] < c2["open"]
                            c3_r = c3["close"] < c3["open"]
                            c4_g = c4["close"] > c4["open"]
                            
                            # 1. Alert for 3 Consecutive Candles
                            if c2_r and c3_r and c4_r and alerted_3_epoch != current_epoch:
                                send_telegram_msg(f"⚠️ *PATTERN ALERT ({symbol})*\n🔴🔴🔴 පිටපිට රතු Candles 3ක් හැදුණා!\n🎯 ඊළඟ Candle එක කොළ වුණොත් BUY Signal එකක් එනු ඇත.")
                                alerted_3_epoch = current_epoch
                                
                            elif c2_g and c3_g and c4_g and alerted_3_epoch != current_epoch:
                                send_telegram_msg(f"⚠️ *PATTERN ALERT ({symbol})*\n🟢🟢🟢 පිටපිට කොළ Candles 3ක් හැදුණා!\n🎯 ඊළඟ Candle එක රතු වුණොත් SELL Signal එකක් එනු ඇත.")
                                alerted_3_epoch = current_epoch

                            # 2. Complete 4-Candle Pattern Reversal Signals
                            if c1_r and c2_r and c3_r and c4_g:
                                min_low = min(c1["low"], c2["low"], c3["low"])
                                send_telegram_msg(
                                    f"🟢 *BUY / HIGHER SIGNAL*\n\n"
                                    f"📊 *Market:* {symbol}\n"
                                    f"🕯️ *Pattern:* 🔴🔴🔴🟢 (Support Reversal)\n"
                                    f"🎯 *Support Level:* {min_low}\n"
                                    f"⚡ *Action:* Open HIGHER Trade Now!"
                                )
                                
                            elif c1_g and c2_g and c3_g and c4_r:
                                max_high = max(c1["high"], c2["high"], c3["high"])
                                send_telegram_msg(
                                    f"🔴 *SELL / LOWER SIGNAL*\n\n"
                                    f"📊 *Market:* {symbol}\n"
                                    f"🕯️ *Pattern:* 🟢🟢🟢🔴 (Resistance Reversal)\n"
                                    f"🎯 *Resistance Level:* {max_high}\n"
                                    f"⚡ *Action:* Open LOWER Trade Now!"
                                )
                                
                            last_epoch = current_epoch
                            
                            # Candle එක Buffer එකට එකතු කිරීම
                            candles_list.append({
                                "open": float(ohlc["open"]),
                                "high": float(ohlc["high"]),
                                "low": float(ohlc["low"]),
                                "close": float(ohlc["close"]),
                                "epoch": ohlc["open_time"]
                            })
                            if len(candles_list) > 30:
                                candles_list.pop(0)

        except Exception as e:
            await asyncio.sleep(5)

async def start_all_monitors():
    send_telegram_msg("🚀 *Deriv Signal Engine Updated & Fixed 24/7!*")
    tasks = [monitor_symbol(sym) for sym in SYMBOLS]
    await asyncio.gather(*tasks)

def run_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_all_monitors())

t = threading.Thread(target=run_async_loop, daemon=True)
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
