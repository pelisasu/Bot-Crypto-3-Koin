import os
import requests
import joblib
import numpy as np
import pandas as pd
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CryptoExecution:
    def __init__(self, symbol="BTCUSDT"):
        self.symbol = symbol.upper()
        self.model_file = f"model_{self.symbol}.pkl"
        self.state_file = f"state_{self.symbol}.json"
        self.model, self.scaler = self._safe_load(self.model_file)

    def _safe_load(self, path):
        if path and os.path.exists(path):
            try:
                loaded_data = joblib.load(path)
                if isinstance(loaded_data, tuple):
                    logging.info(f"🧠 Crypto AI: Model & Scaler sukses dimuat pikeun {self.symbol}!")
                    return loaded_data[0], loaded_data[1]
                else:
                    return loaded_data, None
            except Exception as e:
                logging.warning(f"⚠️ Gagal muat model {self.symbol}: {e}")
        return None, None

    def calculate_rsi(self, series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, series, slow=26, fast=12, signal=9):
        exp1 = series.ewm(span=fast, adjust=False).mean()
        exp2 = series.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram

    def get_signal(self, df: pd.DataFrame) -> str:
        if df.empty or len(df) < 210 or self.model is None:
            return None

        close = df['Close']
        open_p = df['Open']
        high = df['High']
        low = df['Low']

        ma200 = close.rolling(window=200).mean().iloc[-1]
        ma50 = close.rolling(window=50).mean().iloc[-1]
        current_price = close.iloc[-1]

        tr = np.maximum(high.values[1:] - low.values[1:], np.maximum(abs(high.values[1:] - close.values[:-1]), abs(low.values[1:] - close.values[:-1])))
        atr = float(pd.Series(tr).rolling(14).mean().iloc[-1])
        
        rsi_s = self.calculate_rsi(close, 14)
        rsi = float(rsi_s.iloc[-1]) if not rsi_s.empty else 50.0
        
        _, _, macd_hist_series = self.calculate_macd(close)
        macd_hist = float(macd_hist_series.iloc[-1]) if not macd_hist_series.empty else 0.0
        
        body_size = abs(current_price - open_p.iloc[-1])

        is_buy_setup = (current_price > ma200) and (ma50 > ma200) and (rsi > 50)
        is_sell_setup = (current_price < ma200) and (ma50 < ma200) and (rsi < 50)

        try:
            features = np.array([[
                float(atr), 
                float(body_size), 
                float(current_price - ma200), 
                float(macd_hist),
                float(rsi),
                float(ma50 - ma200)
            ]])
            
            if self.scaler is not None:
                features = self.scaler.transform(features)
            
            pred = self.model.predict(features)[0]
            
            if is_buy_setup and pred == 1:
                return "BUY"
            elif is_sell_setup and pred == 0:
                return "SELL"
        except Exception as e:
            logging.warning(f"AI Prediction Error dina {self.symbol}: {e}")

        return None

    def is_spam(self, signal: str) -> bool:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    last_sig = json.load(f).get("signal", None)
                    if last_sig == signal:
                        return True
            except: pass
        return False

    def send_notification(self, signal: str, current_price: float):
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not token or not chat_id: return

        # Format kartu bewara dipoles supados jelas harga real-time na
        card = (
            f"🚀💥 *[CRYPTO MASTERMIND SNIPER]* 💥🚀\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"🪙 *Koin*: `{self.symbol}`\n"
            f"🔥 *EKSEKUSI*: `STRONG {signal}`\n"
            f"💵 *Harga Real (Yahoo/MT5)*: `{current_price:.2f}`\n"
            "-------------------------------------\n"
            f"📊 *Status*: Sinyal AI Terverifikasi\n"
            f"💡 *Catetan*: Cek chart MT5 anjeun di kisaran harga ieu."
        )
        
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": card, "parse_mode": "Markdown"}, timeout=5)
            with open(self.state_file, "w") as f:
                json.dump({"signal": signal}, f)
        except Exception as e:
            logging.warning(f"Gagal kirim Telegram: {e}")
