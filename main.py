import asyncio
import json
import requests
import websockets

# මෙතනට ඔයාගේ ඇත්තම ටෝකන් එක සහ චැට් අයිඩී එක Quotes (" ") ඇතුළට දාන්න
TELEGRAM_BOT_TOKEN = "8609436988:AAEEcnQgqZtlWPcOvMHgJGPhK8pTAz-TBeQ"
TELEGRAM_CHAT_ID = "5573340878"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload)
        print("Telegram Response:", response.text)
    except Exception as e:
        print(f"Telegram Error: {e}")

async def monitor_deriv():
    print("Starting bot and sending telegram message...")
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
