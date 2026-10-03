import ccxt
import pandas as pd
from indicators import add_all_indicators

# Configurar exchange (datos públicos, no requiere API key para leer velas)
exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True,
})

print("Descargando velas de BTC/USDT...")
# Pedimos 300 velas de 1 hora para que los indicadores tengan suficientes datos
ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=300)

# Convertimos a DataFrame de Pandas
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

print("Calculando indicadores...")
df = add_all_indicators(df)

print("\n--- ÚLTIMAS 3 VELAS CON INDICADORES ---")
print(df[['timestamp', 'close', 'sma_50', 'sma_200', 'rsi_14', 'atr_14']].tail(3))