# /home/ubuntu/trendguard/indicators.py
import pandas as pd
import numpy as np

def calculate_sma(df, period=200):
    return df['close'].rolling(window=period).mean()

def calculate_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(window=period).mean()

def calculate_donchian(df, period=55):
    df['high_55'] = df['high'].rolling(window=period).max().shift(1)
    df['low_55'] = df['low'].rolling(window=period).min().shift(1)
    return df

def add_all_indicators(df):
    df['sma_200'] = calculate_sma(df, 200)
    df['atr_14'] = calculate_atr(df, 14)
    df = calculate_donchian(df, 55)
    return df