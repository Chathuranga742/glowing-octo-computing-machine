import os
import time
import threading
import json
import websocket
from flask import Flask, render_template_string

app = Flask(__name__)

# Deriv Volatility Indices 10
ASSETS = {
    "R_10": "Volatility 10 Index",
    "R_25": "Volatility 25 Index",
    "R_50": "Volatility 50 Index",
    "R_75": "Volatility 75 Index",
    "R_100": "Volatility 100 Index",
    "1HZ10V": "Volatility 10 (1s) Index",
    "1HZ25V": "Volatility 25 (1s) Index",
    "1HZ50V": "Volatility 50 (1s) Index",
    "1HZ75V": "Volatility 75 (1s) Index",
    "1HZ100V": "Volatility 100 (1s) Index"
}

latest_candles = {}
signals_log = []  # Screen එකේ පෙන්නන්න සිග්නල් ටික සේව් කරගන්න ලિස්ට් එකක්

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Deriv Reversal Signals Bot</title>
    <meta http-equiv="refresh" content="5"> <!-- තත්පර 5න් 5ට page එක auto refresh වෙයි -->
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background-color: #121212; color: #ffffff; text-align: center; padding: 20px; }
        h1 { color: #00ffcc; }
        .status { color: #00ff00; font-weight: bold; margin-bottom: 20px; }
        table { width: 100%; max-width: 800px; margin: 0 auto; border-collapse: collapse; background: #1e1e1e; border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px; border-bottom: 1px solid #333; text-align: center; }
        th { background-color: #333; color: #ffcc00; }
        .buy { color: #00ff00; font-weight: bold; }
        .sell { color: #ff3333; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🚀 Deriv Live Reversal Signals Dashboard</h1>
    <div class="status">● Bot is Running 24/7 (Auto-updating every 5s)</div>
    
    <table>
        <tr>
            <th>Time</th>
            <th>Asset</th>
            <th>Pattern</th>
            <th>Action</th>
        </tr>
        {% if signals %}
            {% for sig in signals %}
            <tr>
                <td>{{ sig.time }}</td>
                <td>{{ sig.asset }}</td>
                <td>{{ sig.pattern }}</td>
                <td class="{{ 'buy' if 'BUY' in sig.action else 'sell' }}">{{ sig.action }}</td>
            </tr>
            {% endfor %}
        {% else %}
            <tr>
                <td colspan="4" style="color: #888;">Waiting for market reversal patterns... (Make sure market is open)</td>
            </tr>
        {% endif %}
    </table>
</body>
</html>
"""

def on_message(ws, message):
    try:
        data = json.loads(message)
        if "ohlc" in data:
            candle = data["ohlc"]
            symbol = candle["symbol"]
            open_p = float(candle.get("open", 0))
            close_p = float(candle.get("close", 0))
            
            color = "🟢" if close_p >= open_p else "🔴"
            
            if symbol not in latest_candles:
                latest_candles[symbol] = []
                
            latest_candles[symbol].append(color)
            if len(latest_candles[symbol]) > 5:
                latest_candles[symbol].pop(0)
                
            history = latest_candles[symbol]
            if len(history) >= 3:
                p1, p2, p3 = history[-3], history[-2], history[-1]
                if (p1 == "🔴" and p2 == "🔴" and p3 == "🟢") or (p1 == "🟢" and p2 == "🟢" and p3 == "🔴"):
                    signal_type = "BUY (CALL)" if p3 == "🟢" else "SELL (PUT)"
                    
                    # Current time format
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    
                    signal_entry = {
                        "time": current_time,
                        "asset": ASSETS.get(symbol, symbol),
                        "pattern": f"{p1} {p2} {p3}",
                        "action": signal_type
                    }
                    
                    # අලුත්ම සිග්නල් එක උඩින්ම වැටෙන්න දාමු
                    signals_log.insert(0, signal_entry)
                    if len(signals_log) > 20:  # උපරිම සිග්නල් 20ක් විතරක් ස්ක්‍රීන් එකේ තියාගමු
                        signals_log.pop()
                        
    except Exception as e:
        print(f"WS Error: {e}")

def on_error(ws, error):
    print(f"WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket Closed. Reconnecting...")
    time.sleep(5)
    start_websocket()

def on_open(ws):
    print("Connected to Deriv WebSocket! Subscribing to assets...")
    for symbol in ASSETS.keys():
        sub_req = {"sub_ticks_history": symbol, "style": "candles", "granularity": 60}
        ws.send(json.dumps(sub_req))

def start_websocket():
    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://ws.derivws.com/websockets/v3?app_id=1089",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever()
        except Exception as e:
            print(f"WS Loop Error: {e}")
            time.sleep(5)

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML_TEMPLATE, signals=signals_log)

if __name__ == "__main__":
    # Start Deriv WebSocket Thread
    ws_thread = threading.Thread(target=start_websocket, daemon=True)
    ws_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
