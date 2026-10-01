"""
Test de conexion con Binance Futures Demo Trading.
No toca bot.py ni el servicio systemd.
"""

from config import (
    BINANCE_API_KEY, BINANCE_API_SECRET, BINANCE_TESTNET,
    SYMBOL, TIMEFRAME
)
import ccxt

print("=" * 50)
print("TEST DE CONEXION TRENDGUARD - FASE 2")
print("=" * 50)

# 1. Verificar que las keys se cargaron
print(f"\n[1] Testnet activo: {BINANCE_TESTNET}")
print(f"[1] API Key cargada: {BINANCE_API_KEY[:8]}...{BINANCE_API_KEY[-4:]}")
print(f"[1] Secret cargado: {'SI' if BINANCE_API_SECRET else 'NO'}")

# 2. Crear cliente ccxt
print("\n[2] Creando cliente ccxt (binanceusdm)...")
exchange = ccxt.binanceusdm({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'},
})

if BINANCE_TESTNET:
    exchange.enable_demo_trading(True)
    print("[2] Demo trading mode ACTIVADO")
else:
    print("[2] ADVERTENCIA - MODO REAL")

# 3. Probar ticker (publico, no requiere auth)
print(f"\n[3] Probando fetch_ticker de {SYMBOL}...")
try:
    ticker = exchange.fetch_ticker(SYMBOL)
    print(f"    OK BTC precio: ${ticker['last']:,.2f}")
except Exception as e:
    print(f"    ERROR: {e}")

# 4. Probar balance (privado, SI requiere auth)
print("\n[4] Probando fetch_balance (requiere auth)...")
try:
    balance = exchange.fetch_balance()
    usdt = balance.get('USDT', {})
    print(f"    OK USDT libre: {usdt.get('free', 0)}")
    print(f"    OK USDT total: {usdt.get('total', 0)}")
except Exception as e:
    print(f"    ERROR: {e}")

# 5. Probar velas historicas
print(f"\n[5] Probando fetch_ohlcv ({TIMEFRAME}, 5 velas)...")
try:
    ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=5)
    print(f"    OK {len(ohlcv)} velas obtenidas")
    print(f"    Ultima vela: {ohlcv[-1]}")
except Exception as e:
    print(f"    ERROR: {e}")

print("\n" + "=" * 50)
print("FIN DEL TEST")
print("=" * 50)