import asyncio
import json
import os
import threading
import requests
import websockets
from flask import Flask

# 1. Dummy Web Server to keep Render Web Service alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Deriv Bot is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 2. Telegram Details
TELEGRAM_BOT_TOKEN = "8609436988:AAEEcnQgqZtlWPcOvMHgJGPhK8pTAz-TBeQ"
TELEGRAM_CHAT_ID = "5573340878"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Telegram error:", e)

# 3. Deriv WebSocket Logic
async def connect_deriv():
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    while True:
        try:
            async with websockets.connect(uri, extra_headers=headers) as websocket:
                print("Connected to Deriv WebSocket successfully!")
                send_telegram_msg("🚀 Deriv Signal Bot Connected Successfully & Monitoring 24/7!")
                
                while True:
                    await websocket.send(json.dumps({"ping": 1}))
                    await asyncio.sleep(30)
                    
        except Exception as e:
            print(f"Connection error: {e}. Retrying in 10 seconds...")
            await asyncio.sleep(10)

def start_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(connect_deriv())

if __name__ == "__main__":
    threading.Thread(target=start_bot_thread, daemon=True).start()
    run_flask()
