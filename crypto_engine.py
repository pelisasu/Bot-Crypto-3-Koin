import pandas as pd
import numpy as np
import joblib
import os
import logging
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class CryptoBrain:
    def __init__(self, symbol="BTCUSDT"):
        self.symbol = symbol.upper()
        # Robah format simbol Binance (BTCUSDT) jadi format Yahoo Finance (BTC-USD)
        self.yf_symbol = self.symbol.replace("USDT", "-USD")
        self.history_file = f"history_{self.symbol}.csv"
        self.model_file = f"model_{self.symbol}.pkl"

    def fetch_data(self):
        """Nyokot data candlestick tina Yahoo Finance"""
        try:
            logging.info(f"Narik data {self.yf_symbol} tina Yahoo Finance...")
            # Tarik data sajarah per jam (1h)
            ticker = yf.Ticker(self.yf_symbol)
            df = ticker.history(period="5d", interval="60m")
            
            if df.empty:
                # Coba cara kadua bilih interval 60m teu kabaca
                df = ticker.history(period="7d", interval="1h")
                
            if df.empty:
                logging.error(f"Data Yahoo Finance keur {self.yf_symbol} kosong!")
                return pd.DataFrame()
                
            # Ambil kolom anu diperlukeun wungkul
            df = df[['Open', 'High', 'Low', 'Close']].dropna()
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
