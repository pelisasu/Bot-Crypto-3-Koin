import os
import logging
import requests
from crypto_engine import CryptoBrain
from crypto_execution import CryptoExecution

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_telegram_msg(text):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=5)
    except Exception as e:
        logging.warning(f"Gagal kirim pesan Telegram: {e}")

def run_crypto_bot():
    coins = ["BTCUSDT", "SOLUSDT", "ETHUSDT"]
    
    # Kirim béwara sakali yen bot mimiti aktif/jalan
    send_telegram_msg("🟢 *Crypto Bot 24/7 Sniper* Aktif & Sedang Memindai Pasar (BTC, SOL, ETH)...")

    for coin in coins:
        logging.info(f"=== Mulai mariksa pasar {coin} ===")
        try:
            brain = CryptoBrain(coin)
            executor = CryptoExecution(coin)
            
            # 1. Tarik data candlestick tina Yahoo Finance
            df = brain.fetch_data()
            if df.empty:
                logging.warning(f"Data {coin} kosong atawa gagal ditarik tina Yahoo Finance!")
                continue
                
            # 2. Update Otak AI
            brain.update_brain(df)
            
            current_price = df['Close'].iloc[-1]
            
            # 3. Candak Sinyal AI
            signal = executor.get_signal(df)
            if not signal:
                logging.info(f"Sinyal keur {coin} teu acan kabentuk. Harga: {current_price}")
                continue
                
            logging.info(f"Sinyal kabaca pikeun {coin}: {signal} | Harga: {current_price}")
            
            # 4. Cek Anti-Spam & Kirim Telegram (Mencegah notif berulang jika sinyal sama)
            if executor.is_spam(signal):
                logging.info(f"{coin}: Sinyal masih tetep {signal}. Teu spam notif.")
            else:
                executor.send_notification(signal, current_price)
                logging.info(f"🔥 SUKSES: Sinyal anyar {coin} ({signal}) dikirim ka Telegram!")
                
        except Exception as e:
            logging.error(f"Error lumangsung dina koin {coin}: {e}")

if __name__ == "__main__":
    run_crypto_bot()
