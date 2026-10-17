import asyncio
import json
import websockets
import requests

# ==================== SETTINGS ====================
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" # Token එක මෙතනට දාන්න
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID" # Chat ID එක මෙතනට දාන්න

# Check කරන්න ඕන Volatility Indices ලැයිස්තුව
SYMBOLS = [
"R_10", "R_25", "R_50", "R_75", "R_100",
"1HZ10V", "1HZ25V", "1HZ50V", "1HZ75V", "1HZ100V"
]

def send_telegram_signal(message):
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
try:
requests.post(url, json=payload)
except Exception as e:
print(f"Error sending Telegram message: {e}")

async def check_symbol_strategy(symbol):
url = "wss://ws.derivws.com/websockets/v3?app_id=1089"

try:
async with websockets.connect(url) as ws:
req = {
"ticks_history": symbol,
"adjust_start_time": 1,
"count": 10,
"end": "latest",
"granularity": 60,
"style": "candles"
}
await ws.send(json.dumps(req))
res = await ws.recv()
data = json.loads(res)

if "candles" in data:
candles = data["candles"]
if len(candles) < 5:
return

c1 = candles[-5]
c2 = candles[-4]
c3 = candles[-3]
c4 = candles[-2]

is_green = lambda c: c['close'] > c['open']
is_red = lambda c: c['close'] < c['open']

recent_high = max([c['high'] for c in candles[:-2]])
recent_low = min([c['low'] for c in candles[:-2]])

# 3 Green Candles + Resistance -> Red Candle Signal (SELL)
if is_green(c1) and is_green(c2) and is_green(c3):
if c3['high'] >= recent_high and is_red(c4):
msg = (f"🔴 *SELL SIGNAL ALERT!*\n\n"
f"📊 *Asset:* {symbol}\n"
f"🕯️ *Pattern:* 3 Green + Resistance Reversal\n"
f"⏰ *Timeframe:* 1 Minute\n"
f"➡️ *Direction:* FALL / PUT")
print(f"Signal Found: {symbol} - SELL")
send_telegram_signal(msg)

# 3 Red Candles + Support -> Green Candle Signal (BUY)
elif is_red(c1) and is_red(c2) and is_red(c3):
if c3['low'] <= recent_low and is_green(c4):
msg = (f"🟢 *BUY SIGNAL ALERT!*\n\n"
f"📊 *Asset:* {symbol}\n"
f"🕯️ *Pattern:* 3 Red + Support Reversal\n"
f"⏰ *Timeframe:* 1 Minute\n"
f"➡️ *Direction:* RISE / CALL")
print(f"Signal Found: {symbol} - BUY")
send_telegram_signal(msg)
except Exception as e:
print(f"Connection error for {symbol}: {e}")

async def main():
print("🚀 Deriv Signal Bot is Running...")
send_telegram_signal("🚀 *Deriv Signal Bot Connected!* Monitoring Volatility Indices 24/7...")

while True:
for symbol in SYMBOLS:
await check_symbol_strategy(symbol)
await asyncio.sleep(1)

await asyncio.sleep(60)

if name == "main":
asyncio.run(main())
