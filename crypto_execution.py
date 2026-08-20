import json
import os
import joblib
import requests

class CryptoExecution:
    def __init__(self, symbol="BTCUSDT"):
        self.symbol = symbol.upper()
        self.state_file = f"state_{self.symbol}.json"
        self.model_file = f"model_{self.symbol}.pkl"
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def get_signal(self, current_data):
        if not os.path.exists(self.model_file): return None
        model = joblib.load(self.model_file)
        X_input = current_data.iloc[[-1]].values
        prediction = model.predict(X_input)
        return "BUY" if prediction[0] == 1 else "SELL"

    def is_spam(self, new_signal):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                last_sig = json.load(f).get("signal")
                if last_sig == new_signal: return True
        return False

    def send_notification(self, signal, price):
        # Target TP/SL dinamis dumasar koin
        spread = price * 0.015 # 1.5% range
        tp = price + spread if signal == "BUY" else price - spread
        sl = price - (spread / 2) if signal == "BUY" else price + (spread / 2)
        
        msg = (f"🚀 *CRYPTO SNIPER SIGNAL: {self.symbol}*\n"
               f"🎯 *Signal*: {signal}\n"
               f"💵 *Price*: ${price:,.2f}\n"
               f"🎯 *TP*: ${tp:,.2f}\n"
               f"🛑 *SL*: ${sl:,.2f}")
        
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        requests.post(url, json={"chat_id": self.chat_id, "text": msg, "parse_mode": "Markdown"})
        
        with open(self.state_file, 'w') as f:
            json.dump({"signal": signal}, f)
