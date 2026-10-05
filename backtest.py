# /home/ubuntu/trendguard/backtest.py
import ccxt
import pandas as pd
from indicators import add_all_indicators
from strategy import generate_signal, calculate_position_size

SYMBOL = 'BTC/USDT'
TIMEFRAME = '1d'
LIMIT = 2000
BALANCE_INICIAL = 5000.0
RIESGO = 0.02
COMISION = 0.0005

def descargar_datos(symbol, timeframe, limit):
    exchange = ccxt.binance()
    print(f"Descargando {limit} velas de {symbol} en {timeframe}...", flush=True)
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def ejecutar_backtest():
    print("--- INICIANDO BACKTEST DEFINITIVO ---", flush=True)
    df = descargar_datos(SYMBOL, TIMEFRAME, LIMIT)
    df = add_all_indicators(df)
    
    balance = BALANCE_INICIAL
    position = None
    entry_price = 0.0
    max_price = 0.0
    min_price = 0.0
    cantidad = 0.0
    trades = []
    
    for i in range(200, len(df)):
        df_actual = df.iloc[:i+1]
        last_row = df_actual.iloc[-1]
        current_price = last_row['close']
        
        signal, price, mensaje = generate_signal(
            df_actual, current_position=position, entry_price=entry_price,
            max_price=max_price, min_price=min_price
        )
        
        if signal == 'buy':
            atr = last_row['atr_14']
            stop_loss = price - (3.0 * atr)
            cantidad = calculate_position_size(balance, RIESGO, price, stop_loss)
            position = 'long'
            entry_price = price
            max_price = price
            min_price = None
            trades.append({'tipo': 'OPEN LONG', 'precio': round(price, 2), 'balance': round(balance, 2)})
            
        elif signal == 'sell':
            atr = last_row['atr_14']
            stop_loss = price + (3.0 * atr)
            cantidad = calculate_position_size(balance, RIESGO, price, stop_loss)
            position = 'short'
            entry_price = price
            min_price = price
            max_price = None
            trades.append({'tipo': 'OPEN SHORT', 'precio': round(price, 2), 'balance': round(balance, 2)})
            
        elif signal == 'close_long':
            pnl = (price - entry_price) * cantidad
            costo = (entry_price * cantidad * COMISION) + (price * cantidad * COMISION)
            pnl_neto = pnl - costo
            balance += pnl_neto
            trades.append({'tipo': 'CLOSE LONG', 'precio': round(price, 2), 'pnl': round(pnl_neto, 2), 'balance': round(balance, 2)})
            position = None
            
        elif signal == 'close_short':
            pnl = (entry_price - price) * cantidad
            costo = (entry_price * cantidad * COMISION) + (price * cantidad * COMISION)
            pnl_neto = pnl - costo
            balance += pnl_neto
            trades.append({'tipo': 'CLOSE SHORT', 'precio': round(price, 2), 'pnl': round(pnl_neto, 2), 'balance': round(balance, 2)})
            position = None

    print("\n--- RESULTADOS DEL BACKTEST ---", flush=True)
    print(f"Balance Inicial: ${BALANCE_INICIAL:.2f}", flush=True)
    print(f"Balance Final:   ${balance:.2f}", flush=True)
    rendimiento = ((balance - BALANCE_INICIAL) / BALANCE_INICIAL) * 100
    print(f"Rendimiento:     {rendimiento:.2f}%", flush=True)
    print(f"Total de Operaciones: {len(trades)}", flush=True)
    if len(trades) > 0:
        print("\nÚltimas 10 operaciones:", flush=True)
        for t in trades[-10:]:
            print(t, flush=True)

ejecutar_backtest()