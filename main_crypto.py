import os
import logging
import requests
from crypto_engine import CryptoBrain
from crypto_execution import CryptoExecution

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def run_crypto_bot():
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    logging.info("=== Mulai Analisis Pasar Crypto Elite AI (BTC, ETH, SOL) ===")
    
    for symbol in symbols:
        logging.info(f"--- Menganalisis {symbol} ---")
        brain = CryptoBrain(symbol)
        executor = CryptoExecution(symbol)
        
        df = brain.fetch_data()
        if df.empty:
            logging.warning(f"Gagal narik data pasar pikeun {symbol}!")
            continue
        
        # Hitung Akurasi Live kalayan safety check
        acc = brain.update_brain(df)
        
        # Pastikeun acc téh angka (float/int), upami None jadikeun 0.0
        if acc is None:
            acc = 0.0
            
        current_price = float(df['Close'].iloc[-1])
        
        # Log status live di console
        status_msg = f"🟢 Bot Elite Crypto {symbol} Aktif | Akurasi Live: {acc*100:.2f}% | Harga: {current_price:.2f}"
        logging.info(status_msg)
        
        # Logika Sinyal
        if acc >= 0.80:
            try:
                if hasattr(executor, 'get_signal'):
                    signal, price, sl, tp = executor.get_signal(df)
                    if signal and not executor.is_spam(signal):
                        executor.send_notification(signal, price, sl, tp)
                        logging.info(f"🔥 Sinyal {symbol} {signal} dikirim!")
                    else:
                        logging.info(f"Pola entry {symbol} teu acan singkron atanapi masih anti-spam.")
            except Exception as e:
                logging.info(f"Catetan Eksekusi Sinyal {symbol}: {e}")
        else:
            logging.info(f"⚠️ Akurasi {symbol} handap ({acc*100:.2f}% < 80%). Sinyal ditahan.")

if __name__ == "__main__":
    run_crypto_bot()
