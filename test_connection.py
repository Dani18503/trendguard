# /home/ubuntu/trendguard/test_connection.py
import os
import ccxt
from dotenv import load_dotenv

# ✅ Cargar ruta absoluta para que siempre encuentre el .env
load_dotenv('/home/ubuntu/trendguard/.env')

print("TEST DE CONEXION TRENDGUARD - FASE 2")
print("=====================================")

api_key = os.getenv('BINANCE_API_KEY')
secret = os.getenv('BINANCE_SECRET')
testnet = os.getenv('BINANCE_TESTNET')

print(f"[1] Testnet activo: {testnet}")
print(f"[1] API Key cargada: {api_key[:8]}...{api_key[-4:]}" if api_key else "[1] API Key cargada: NO")
print(f"[1] Secret cargado: {'SI' if secret else 'NO'}")

exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': secret,
    'options': {'defaultType': 'future'},
    'enableRateLimit': True,
})
exchange.enable_demo_trading(True)
print("[2] Demo trading mode ACTIVADO")

try:
    ticker = exchange.fetch_ticker('BTC/USDT:USDT')
    print(f"[3] OK BTC precio: ${ticker['last']:.2f}")
except Exception as e:
    print(f"[3] Error fetch_ticker: {e}")

try:
    balance = exchange.fetch_balance()
    usdt = balance['USDT']['free']
    print(f"[4] USDT libre: {usdt}")
except Exception as e:
    print(f"[4] ERROR: {e}")

print("=====================================")
print("FIN DEL TEST")