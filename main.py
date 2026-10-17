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

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(">>> Telegram Response:", res.json())
    except Exception as e:
        print(">>> Telegram Request Error:", e)

@app.route('/')
def home():
    return "Deriv Bot is Running 24/7!"

async def connect_deriv():
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    while True:
        try:
            print(">>> Connecting to Deriv WebSocket...")
            async with websockets.connect(uri, extra_headers=headers) as websocket:
                print(">>> Connected to Deriv WebSocket successfully!")
                
                # Telegram Message එක යවනවා
                send_telegram_msg("🚀 Deriv Signal Bot Connected Successfully & Monitoring 24/7!")
                
                while True:
                    await websocket.send(json.dumps({"ping": 1}))
                    await asyncio.sleep(30)
                    
        except Exception as e:
            print(f">>> WebSocket Error: {e}. Retrying in 10s...")
            await asyncio.sleep(10)

def start_background_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(connect_deriv())

# Thread එක මෙතනදීම කෙලින්ම Start කරනවා
bot_thread = threading.Thread(target=start_background_loop)
bot_thread.daemon = True
bot_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
