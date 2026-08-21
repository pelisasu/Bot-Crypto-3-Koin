# ... (tambahkeun di handap fungsi get_signal sateuacanna)

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
        return False  # <--- DIBENERKEUN DI DIEU (tadinya FALSE)

    def get_signal(self, df: pd.DataFrame):
        if df.empty or len(df) < 60 or self.model is None:
            return None, 0, 0, 0

        df_ind = self.calculate_indicators(df)
        row = df_ind.iloc[-1]
        
        current_price = float(row['Close'])
        atr = float(row['ATR'])
        
        # LOGIKA DIPERLONGGAR SUPAYA SINYAL GAMPANG KELUAR
        # RSI 40-60 (bukan 48-52)
        is_buy_setup = (current_price > row['MA20']) and (row['RSI'] > 40)
        is_sell_setup = (current_price < row['MA20']) and (row['RSI'] < 60)

        try:
            features = np.array([[
                atr, float(row['BodySize']), current_price - row['MA20'], 
                float(row['MACD_Hist']), float(row['RSI']), row['MA20'] - row['MA50']
            ]])
            
            if self.scaler is not None:
                features = self.scaler.transform(features)
            
            pred = self.model.predict(features)[0]
            
            # TP/SL Dinamis
            sl_distance = atr * 1.5
            tp_distance = atr * 3.0

            if is_buy_setup and pred == 1:
                return "BUY", current_price, current_price - sl_distance, current_price + tp_distance
            elif is_sell_setup and pred == 0:
                return "SELL", current_price, current_price + sl_distance, current_price - tp_distance
                
        except Exception as e:
            logging.warning(f"AI Prediction Error {self.symbol}: {e}")

        return None, 0, 0, 0
