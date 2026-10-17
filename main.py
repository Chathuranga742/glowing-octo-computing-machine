import asyncio
import json
import os
import requests
import websockets

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_msg(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram tokens not set!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

async def monitor_deriv():
    send_telegram_msg("🚀 Deriv Signal Bot Connected! Monitoring Volatility Indices 24/7...")
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    
    async with websockets.connect(uri) as websocket:
        req = {
            "ticks_history": "R_100",
            "adjust_start_time": 1,
            "count": 5,
            "end": "latest",
            "style": "candles",
            "granularity": 60,
            "subscribe": 1
        }
        await websocket.send(json.dumps(req))
        
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            if "ohlc" in data:
                ohlc = data["ohlc"]
                open_price = float(ohlc["open"])
                close_price = float(ohlc["close"])
                
                if close_price > open_price:
                    print(f"Bullish candle detected: {close_price}")
            await asyncio.sleep(1)

asyncio.run(monitor_deriv())
