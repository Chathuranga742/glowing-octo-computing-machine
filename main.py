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

@app.route('/')
def home():
    return "Deriv 3-Candle Strategy Bot is Active!"

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
                
                candles = []
                last_processed_epoch = 0
                alerted_epochs = set()
                
                while True:
                    response = json.loads(await websocket.recv())
                    
                    if "candles" in response:
                        candles = response["candles"]
                        
                    elif "ohlc" in response:
                        ohlc = response["ohlc"]
                        current_epoch = ohlc["open_time"]
                        
                        # Process when candle closes
                        if current_epoch != last_processed_epoch:
                            if len(candles) >= 4:
                                c1 = candles[-3] # 3rd oldest
                                c2 = candles[-2] # 2nd oldest
                                c3 = candles[-1] # Newly closed 3rd candle
                                
                                is_c1_green = c1["close"] > c1["open"]
                                is_c2_green = c2["close"] > c2["open"]
                                is_c3_green = c3["close"] > c3["open"]
                                
                                is_c1_red   = c1["close"] < c1["open"]
                                is_c2_red   = c2["close"] < c2["open"]
                                is_c3_red   = c3["close"] < c3["open"]
                                
                                recent_high = max(c1["high"], c2["high"], c3["high"])
                                recent_low  = min(c1["low"], c2["low"], c3["low"])
                                
                                # 🟢🟢🟢 Green 3 Alert
                                if is_c1_green and is_c2_green and is_c3_green:
                                    if current_epoch not in alerted_epochs:
                                        msg = f"⚠️ *PATTERN ALERT ({symbol})*\n🟢🟢🟢 කොළ Candles 3ක් හැදුණා! ඊළඟ Candle එක රතු වුණොත් **SELL** Signal එකක් එනු ඇත.\n🎯 Resistance: {recent_high}"
                                        send_telegram_msg(msg)
                                        alerted_epochs.add(current_epoch)
                                        
                                # 🔴🔴🔴 Red 3 Alert
                                elif is_c1_red and is_c2_red and is_c3_red:
                                    if current_epoch not in alerted_epochs:
                                        msg = f"⚠️ *PATTERN ALERT ({symbol})*\n🔴🔴🔴 රතු Candles 3ක් හැදුණා! ඊළඟ Candle එක කොළ වුණොත් **BUY** Signal එකක් එනු ඇත.\n🎯 Support: {recent_low}"
                                        send_telegram_msg(msg)
                                        alerted_epochs.add(current_epoch)

                                # Full Signal Verification (4th Candle Reversal)
                                if len(candles) >= 5:
                                    c0 = candles[-4]
                                    c1_p = candles[-3]
                                    c2_p = candles[-2]
                                    c3_p = candles[-1] # Current closed 4th candle
                                    
                                    g1 = c0["close"] > c0["open"]
                                    g2 = c1_p["close"] > c1_p["open"]
                                    g3 = c2_p["close"] > c2_p["open"]
                                    r4 = c3_p["close"] < c3_p["open"]
                                    
                                    r1 = c0["close"] < c0["open"]
                                    r2 = c1_p["close"] < c1_p["open"]
                                    r3 = c2_p["close"] < c2_p["open"]
                                    g4 = c3_p["close"] > c3_p["open"]
                                    
                                    if g1 and g2 and g3 and r4:
                                        send_telegram_msg(f"🔴 *SELL SIGNAL ({symbol})*\n🟢🟢🟢🔴 Setup Complete!\n🎯 Resistance Level: {max(c0['high'], c1_p['high'], c2_p['high'])}")
                                    elif r1 and r2 and r3 and g4:
                                        send_telegram_msg(f"🟢 *BUY SIGNAL ({symbol})*\n🔴🔴🔴🟢 Setup Complete!\n🎯 Support Level: {min(c0['low'], c1_p['low'], c2_p['low'])}")

                            last_processed_epoch = current_epoch
                            
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
            await asyncio.sleep(5)

async def start_all_monitors():
    send_telegram_msg("🚀 *Deriv 3-Candle Tracker Activated!*")
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
