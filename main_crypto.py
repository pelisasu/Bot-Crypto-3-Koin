import os
import logging
from crypto_engine import CryptoBrain
from crypto_execution import CryptoExecution

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_crypto_bot():
    coins = ["BTCUSDT", "SOLUSDT", "ETHUSDT"]
    
    for coin in coins:
        logging.info(f"=== Mulai mariksa pasar {coin} ===")
        try:
            brain = CryptoBrain(coin)
            executor = CryptoExecution(coin)
            
            # 1. Tarik data tina Binance
            df = brain.fetch_data()
            if df.empty:
                logging.warning(f"Data {coin} kosong atawa gagal ditarik ti Binance!")
                continue
                
            # 2. Update Otak AI
            brain.update_brain(df)
            
            # 3. Candak Sinyal
            signal = executor.get_signal(df)
            if not signal:
                logging.warning(f"Sinyal keur {coin} teu acan kabentuk.")
                continue
                
            current_price = df['Close'].iloc[-1]
            logging.info(f"Sinyal kabaca pikeun {coin}: {signal} | Harga: {current_price}")
            
            # 4. Cek Anti-Spam & Kirim Telegram
            if executor.is_spam(signal):
                logging.info(f"{coin}: Sinyal masih tetep {signal}. Teu spam notif.")
            else:
                executor.send_notification(signal, current_price)
                logging.info(f"🔥 SUKSES: Sinyal anyar {coin} ({signal}) dikirim ka Telegram!")
                
        except Exception as e:
            logging.error(f"Error lumangsung dina koin {coin}: {e}")

if __name__ == "__main__":
    run_crypto_bot()
