# /home/ubuntu/trendguard/notifier.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_telegram_message(message):
    """Envía un mensaje a Telegram usando las credenciales del .env"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("⚠️ Faltan credenciales de Telegram en .env")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")