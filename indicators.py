# /home/ubuntu/trendguard/indicators.py
import pandas as pd
import numpy as np

def calculate_sma(df, period=50):
    """Calcula la Media Móvil Simple (SMA)."""
    return df['close'].rolling(window=period).mean()

def calculate_rsi(df, period=14):
    """Calcula el Índice de Fuerza Relativa (RSI)."""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    """Calcula el Rango Verdadero Medio (ATR) para volatilidad y trailing stops."""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(window=period).mean()

def add_all_indicators(df):
    """Aplica todos los indicadores al DataFrame y retorna el resultado."""
    df['sma_50'] = calculate_sma(df, 50)
    df['sma_200'] = calculate_sma(df, 200)
    df['rsi_14'] = calculate_rsi(df, 14)
    df['atr_14'] = calculate_atr(df, 14)
    return df