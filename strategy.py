# /home/ubuntu/trendguard/strategy.py
import pandas as pd

def calculate_position_size(balance, risk_per_trade, entry_price, stop_loss_price):
    risk_amount = balance * risk_per_trade
    risk_per_unit = abs(entry_price - stop_loss_price)
    if risk_per_unit == 0:
        return 0
    return risk_amount / risk_per_unit

def generate_signal(df, current_position=None, entry_price=None, max_price=None, min_price=None):
    last_row = df.iloc[-1]
    current_price = last_row['close']
    sma_200 = last_row['sma_200']
    high_55 = last_row['high_55']
    low_55 = last_row['low_55']
    atr = last_row['atr_14']

    if pd.isna(sma_200) or pd.isna(high_55) or pd.isna(atr):
        return 'hold', None, "Esperando datos suficientes..."

    # ==========================================
    # 1. GESTIÓN DE POSICIÓN ABIERTA (LONG)
    # ==========================================
    if current_position == 'long':
        if max_price is None or current_price > max_price:
            max_price = current_price
        trailing_stop = max_price - (3.0 * atr)
        if current_price <= trailing_stop:
            return 'close_long', current_price, f"Trailing Stop en {trailing_stop:.2f}. Cerrando LONG y esperando nueva señal."

    # ==========================================
    # 2. GESTIÓN DE POSICIÓN ABIERTA (SHORT)
    # ==========================================
    elif current_position == 'short':
        if min_price is None or current_price < min_price:
            min_price = current_price
        trailing_stop = min_price + (3.0 * atr)
        if current_price >= trailing_stop:
            return 'close_short', current_price, f"Trailing Stop en {trailing_stop:.2f}. Cerrando SHORT y esperando nueva señal."

    # ==========================================
    # 3. APERTURA DE NUEVA POSICIÓN (Solo si no hay nada abierto)
    # ==========================================
    else:
        # Filtro Macro: Solo operamos en la dirección de la SMA 200
        if current_price > sma_200 and current_price > high_55:
            return 'buy', current_price, f"Ruptura de máximo 55 días en {current_price}. Abriendo LONG"
        elif current_price < sma_200 and current_price < low_55:
            return 'sell', current_price, f"Ruptura de mínimo 55 días en {current_price}. Abriendo SHORT"

    return 'hold', None, "Sin señales. Esperando..."