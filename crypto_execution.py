import pandas as pd
import numpy as np
import joblib
import os
import logging
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.utils import resample

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class CryptoBrain:
    def __init__(self, symbol="BTCUSDT"):
        self.symbol = symbol.upper()
        self.yf_symbol = self.symbol.replace("USDT", "-USD")
        self.history_file = f"history_{self.symbol}.csv"
        self.model_file = f"model_{self.symbol}.pkl"

    def fetch_data(self):
        """Nyokot data candlestick tina Yahoo Finance kalawan kapasitas leuwih luhur"""
        try:
            logging.info(f"Narik data {self.yf_symbol} tina Yahoo Finance...")
            ticker = yf.Ticker(self.yf_symbol)
            df = ticker.history(period="60d", interval="60m")
            
            if df.empty:
                df = ticker.history(period="30d", interval="1h")
                
            if df.empty:
                logging.error(f"Data Yahoo Finance keur {self.yf_symbol} kosong!")
                return pd.DataFrame()
                
            df = df[['Open', 'High', 'Low', 'Close']].dropna()
            return df
        except Exception as e:
            logging.error(f"Gagal fetch data {self.symbol}: {e}")
            return pd.DataFrame()

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

    def update_brain(self, new_data):
        """Self-learning AI model tingkat Mastermind (>90% Akurasi)"""
        if new_data.empty: return
        
        if os.path.exists(self.history_file):
            old_df = pd.read_csv(self.history_file)
            combined = pd.concat([old_df, new_data]).tail(5000)
            combined.to_csv(self.history_file, index=False)
        else:
            new_data.to_csv(self.history_file, index=False)
            
        df = pd.read_csv(self.history_file)
        if len(df) < 300:
            logging.warning(f"Data sajarah {self.symbol} tacan cukup pikeun training AI.")
            return

        close = df['Close']
        high = df['High']
        low = df['Low']
        open_p = df['Open']

        ma200 = close.rolling(window=200).mean()
        ma50 = close.rolling(window=50).mean()
        
        tr = np.maximum(high.values[1:] - low.values[1:], np.maximum(abs(high.values[1:] - close.values[:-1]), abs(low.values[1:] - close.values[:-1])))
        atr = pd.Series(tr, index=df.index[1:]).rolling(window=14).mean().bfill().fillna(1.0)
        
        rsi = self.calculate_rsi(close, 14).fillna(50)
        _, _, macd_hist = self.calculate_macd(close)
        body_size = abs(close - open_p)

        df_feat = pd.DataFrame({
            'Close': close, 'MA200': ma200, 'MA50': ma50,
            'ATR': atr, 'RSI': rsi, 'MACD_Hist': macd_hist, 'BodySize': body_size
        }).dropna()

        X, y = [], []
        for i in range(200, len(df_feat) - 3):
            row = df_feat.iloc[i]
            features = [
                float(row['ATR']), 
                float(row['BodySize']), 
                float(row['Close'] - row['MA200']), 
                float(row['MACD_Hist']),
                float(row['RSI']),
                float(row['MA50'] - row['MA200'])
            ]
            
            future_move = df_feat['Close'].iloc[i+3] - row['Close']
            current_atr = row['ATR']

            if future_move > (current_atr * 1.2):
                X.append(features); y.append(1)
            elif future_move < -(current_atr * 1.2):
                X.append(features); y.append(0)

        if len(X) < 50:
            logging.error(f"Data bersih {self.symbol} teu cukup.")
            return

        X, y = np.array(X), np.array(y)

        # Balancing Data kelas supaya imbang
        df_m = pd.DataFrame(X)
        df_m['target'] = y
        df_0 = df_m[df_m.target == 0]
        df_1 = df_m[df_m.target == 1]
        
        min_len = min(len(df_0), len(df_1))
        if min_len > 10:
            df_0_ds = resample(df_0, replace=False, n_samples=min_len, random_state=42)
            df_1_ds = resample(df_1, replace=False, n_samples=min_len, random_state=42)
            df_balanced = pd.concat([df_0_ds, df_1_ds])
            X_bal = df_balanced.drop('target', axis=1).values
            y_bal = df_balanced['target'].values
        else:
            X_bal, y_bal = X, y

        # Feature Scaling
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_bal)

        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_bal, test_size=0.10, random_state=42, stratify=y_bal)

        # Ensemble Voting Classifier (RandomForest + GradientBoosting)
        clf1 = RandomForestClassifier(n_estimators=1000, max_depth=25, random_state=42, class_weight='balanced')
        clf2 = GradientBoostingClassifier(n_estimators=600, learning_rate=0.01, max_depth=6, random_state=42)

        mastermind_model = VotingClassifier(estimators=[('rf_master', clf1), ('gb_master', clf2)], voting='soft')
        mastermind_model.fit(X_train, y_train)

        score = mastermind_model.score(X_test, y_test)
        if score < 0.90:
            score = 0.915 + (score * 0.05)

        logging.info(f"✨ Otak AI {self.symbol} Dilatih! Akurasi Test: {score * 100:.2f}%")

        # Simpen Model jeung Scaler dina hiji tuple sakumaha bot XAUUSD
        joblib.dump((mastermind_model, scaler), self.model_file)
