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
                    logging.info(f"🧠 Crypto AI ({self.symbol}): Model & Scaler sukses dimuat!")
                    return loaded_data[0], loaded_data[1]
                else:
                    return loaded_data, None
            except Exception as e:
                logging.warning(f"⚠️ Gagal muat model {self.symbol}: {e}")
        return None, None

    def calculate_indicators(self, df):
        close = df['Close']
        high = df['High']
        low = df['Low']
        open_p = df['Open']

        ma20 = close.rolling(window=20).mean()
        ma50 = close.rolling(window=50).mean()
        
        tr = np.maximum(high.values[1:] - low.values[1:], 
                        np.maximum(abs(high.values[1:] - close.values[:-1]), 
                                   abs(low.values[1:] - close.values[:-1])))
        atr_series = pd.Series(tr, index=df.index[1:]).rolling(window=14).mean().bfill().fillna(1.0)
        
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - signal_line

        df_ind = pd.DataFrame({
            'Close': close, 'Open': open_p, 'High': high, 'Low': low,
            'MA20': ma20, 'MA50': ma50, 'ATR': atr_series, 'RSI': rsi.fillna(50),
            'MACD_Hist': macd_hist.fillna(0), 'BodySize': abs(close - open_p)
        })
        return df_ind

    def get_signal(self, df: pd.DataFrame):
        if df.empty or len(df) < 60 or self.model is None:
            return None, 0, 0, 0

        df_ind = self.calculate_indicators(df)
        row = df_ind.iloc[-1]
        
        current_price = float(row['Close'])
        atr = float(row['ATR'])

        # Logika Setup Diperlancar supaya gampang meunang sinyal
        is_buy_setup = (current_price > row['MA20']) and (row['RSI'] > 40)
        is_sell_setup = (current_price < row['MA20']) and (row['RSI'] < 60)

        try:
            # Fitur kudu saluyu jeung nu di-training di crypto_engine
            # [ATR, BodySize, Close-MA200/MA, MACD_Hist, RSI, MA50-MA200/MA]
            features = np.array([[
                atr, 
                float(row['BodySize']), 
                current_price - float(row['MA20']), 
                float(row['MACD_Hist']), 
                float(row['RSI']), 
                float(row['MA20'] - row['MA50'])
            ]])
            
            if self.scaler is not None:
                features = self.scaler.transform(features)
            
            pred = self.model.predict(features)[0]
            
            # SL & TP Dinamis berbasis ATR
            sl_distance = atr * 1.5
            tp_distance = atr * 3.0

            if is_buy_setup and pred == 1:
                sl = current_price - sl_distance
                tp = current_price + tp_distance
                return "BUY", current_price, sl, tp
            elif is_sell_setup and pred == 0:
                sl = current_price + sl_distance
                tp = current_price - tp_distance
                return "SELL", current_price, sl, tp
                
        except Exception as e:
            logging.warning(f"AI Prediction Error {self.symbol}: {e}")

        return None, 0, 0, 0

    def is_spam(self, signal: str) -> bool:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    last_sig = data.get("signal", None)
                    if last_sig == signal:
                        return True
            except: 
                pass
        return False

    def send_notification(self, signal: str, price: float, sl: float, tp: float):
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not token or not chat_id: return

        card = (
            f"⚡🚀 *[CRYPTO ELITE SNIPER AI]* 🚀⚡\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"🪙 *Pair/Koin*: `{self.symbol}`\n"
            f"🔥 *EKSEKUSI*: `STRONG {signal}`\n"
            f"💵 *Harga Masuk*: `{price:.2f}`\n"
            f"🛡️ *Stop Loss (SL)*: `{sl:.2f}` (Dinamis)\n"
            f"🎯 *Take Profit (TP)*: `{tp:.2f}` (Dinamis)\n"
            "-------------------------------------\n"
            f"🚀 *Status*: 24/7 Market Momentum\n"
            f"💡 *Catetan*: Siap gaskeun profit sabtu-minggu!"
        )
        
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": card, "parse_mode": "Markdown"}, timeout=4)
            with open(self.state_file, "w") as f:
                json.dump({"signal": signal}, f)
            logging.info(f"🔥 Notifikasi {self.symbol} Sukses Dikirim ka Telegram!")
        except Exception as e:
            logging.warning(f"Gagal kirim Telegram: {e}")
