import pandas as pd
import numpy as np
import joblib
import os
import requests
import logging
from sklearn.ensemble import RandomForestClassifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class CryptoBrain:
    def __init__(self, symbol="BTCUSDT"):
        self.symbol = symbol.upper()
        self.history_file = f"history_{self.symbol}.csv"
        self.model_file = f"model_{self.symbol}.pkl"

    def fetch_data(self):
        """Nyokot data candlestick tina Binance Public API"""
        url = f"https://api.binance.com/api/v3/klines?symbol={self.symbol}&interval=1h&limit=150"
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            df = pd.DataFrame(data, columns=[
                'Open_time', 'Open', 'High', 'Low', 'Close', 'Volume',
                'Close_time', 'Quote_asset_volume', 'Number_of_trades',
                'Taker_buy_base', 'Taker_buy_quote', 'Ignore'
            ])
            df = df[['Open', 'High', 'Low', 'Close']].astype(float)
            return df
        except Exception as e:
            logging.error(f"Gagal fetch data {self.symbol}: {e}")
            return pd.DataFrame()

    def update_brain(self, new_data):
        """Self-learning AI model"""
        if new_data.empty: return
        
        if os.path.exists(self.history_file):
            old_df = pd.read_csv(self.history_file)
            combined = pd.concat([old_df, new_data]).tail(2000)
            combined.to_csv(self.history_file, index=False)
        else:
            new_data.to_csv(self.history_file, index=False)
            
        df = pd.read_csv(self.history_file)
        df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
        df.dropna(inplace=True)
        
        X = df[['Open', 'High', 'Low', 'Close']]
        y = df['Target']
        
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X, y)
        joblib.dump(model, self.model_file)
        logging.info(f"🧠 Otak AI {self.symbol} suksés di-update!")
