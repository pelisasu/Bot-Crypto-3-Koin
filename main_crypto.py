from crypto_engine import CryptoBrain
from crypto_execution import CryptoExecution
import logging

def run_crypto_bot():
    coins = ["BTCUSDT", "SOLUSDT", "ETHUSDT"]
    
    for coin in coins:
        logging.info(f"--- Ngariksa pasar {coin} ---")
        brain = CryptoBrain(coin)
        executor = CryptoExecution(coin)
        
        df = brain.fetch_data()
        if df.empty:
            continue
            
        brain.update_brain(df)
        signal = executor.get_signal(df)
        current_price = df['Close'].iloc[-1]
        
        if executor.is_spam(signal):
            logging.info(f"{coin}: Sinyal {signal} stabil. Teu spam.")
        else:
            executor.send_notification(signal, current_price)
            logging.info(f"🔥 {coin}: Sinyal anyar {signal} dikirim!")

if __name__ == "__main__":
    run_crypto_bot()
