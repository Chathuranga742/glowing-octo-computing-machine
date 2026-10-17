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

# Monitor කරන Volatility Indices ලැයිස්තුව
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
    return "Deriv Volatility Strategy Bot is Active 24/7!"

async def monitor_symbol(symbol):
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    while True:
        try:
            async with websockets.connect(uri, extra_headers=headers) as websocket:
                # Request 1-minute candles
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
                
                candles = []
                last_processed_epoch = 0
                
                while True:
                    response = json.loads(await websocket.recv())
                    
                    # Initial candles history list
                    if "candles" in response:
                        candles = response["candles"]
                        
                    # Real-time candle updates
                    elif "ohlc" in response:
                        ohlc = response["ohlc"]
                        # We process when a candle closes (epoch changes)
                        if ohlc["open_time"] != last_processed_epoch:
                            if len(candles) >= 5:
                                c1 = candles[-4] # 3rd oldest
                                c2 = candles[-3] # 2nd oldest
                                c3 = candles[-2] # 1st oldest
                                c4 = candles[-1] # Newly closed candle
                                
                                # Candle Colors: Green (close > open), Red (close < open)
                                is_c1_green = c1["close"] > c1["open"]
                                is_c2_green = c2["close"] > c2["open"]
                                is_c3_green = c3["close"] > c3["open"]
                                is_c4_red   = c4["close"] < c4["open"]
                                
                                is_c1_red   = c1["close"] < c1["open"]
                                is_c2_red   = c2["close"] < c2["open"]
                                is_c3_red   = c3["close"] < c3["open"]
                                is_c4_green = c4["close"] > c4["open"]
                                
                                # Resistance / High calculations
                                recent_high = max(c1["high"], c2["high"], c3["high"])
                                recent_low  = min(c1["low"], c2["low"], c3["low"])
                                
                                # Pattern 1: 3 Green Candles + Resistance Reversal -> SELL Signal
                                if is_c1_green and is_c2_green and is_c3_green and is_c4_red:
                                    msg = (
                                        f"🔴 *SELL / LOWER SIGNAL*\n\n"
                                        f"📊 *Market:* {symbol}\n"
                                        f"🕯️ *Pattern:* 🟢🟢🟢🔴 (3 Green + 1 Red Opposite Candle)\n"
                                        f"🎯 *Resistance Level:* {recent_high}\n"
                                        f"⏰ *Timeframe:* 1 Minute\n"
                                        f"⚡ *Action:* Open LOWER Trade!"
                                    )
                                    send_telegram_msg(msg)
                                
                                # Pattern 2: 3 Red Candles + Support Reversal -> BUY Signal
                                elif is_c1_red and is_c2_red and is_c3_red and is_c4_green:
                                    msg = (
                                        f"🟢 *BUY / HIGHER SIGNAL*\n\n"
                                        f"📊 *Market:* {symbol}\n"
                                        f"🕯️ *Pattern:* 🔴🔴🔴🟢 (3 Red + 1 Green Opposite Candle)\n"
                                        f"🎯 *Support Level:* {recent_low}\n"
                                        f"⏰ *Timeframe:* 1 Minute\n"
                                        f"⚡ *Action:* Open HIGHER Trade!"
                                    )
                                    send_telegram_msg(msg)
                                    
                            last_processed_epoch = ohlc["open_time"]
                            
                            # Maintain internal candles buffer
                            candles.append({
                                "open": float(ohlc["open"]),
                                "high": float(ohlc["high"]),
                                "low": float(ohlc["low"]),
                                "close": float(ohlc["close"]),
                                "epoch": ohlc["open_time"]
                            })
                            if len(candles) > 20:
                                candles.pop(0)

        except Exception as e:
            print(f">>> Error in {symbol}: {e}. Retrying in 5s...")
            await asyncio.sleep(5)

async def start_all_monitors():
    send_telegram_msg("🚀 *Deriv Multi-Volatility Bot Activated!*\nMonitoring 1M Candles & Patterns 24/7...")
    tasks = [monitor_symbol(sym) for sym in SYMBOLS]
    await asyncio.gather(*tasks)

def run_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_all_monitors())

# Background thread startup
t = threading.Thread(target=run_async_loop, daemon=True)
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
