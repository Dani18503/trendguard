# /home/ubuntu/trendguard/strategy.py
import pandas as pd

def calculate_position_size(balance, risk_per_trade, entry_price, stop_loss_price):
    """Calcula cuánto comprar/vender basado en el riesgo del 1% de tu balance."""
    risk_amount = balance * risk_per_trade
    risk_per_unit = abs(entry_price - stop_loss_price)
    if risk_per_unit == 0:
        return 0
    return risk_amount / risk_per_unit

def generate_signal(df, current_position=None, entry_price=None, max_price=None, min_price=None):
    """
    Genera señales usando Trailing Stop dinámico con ATR.
    """
    last_row = df.iloc[-1]
    current_price = last_row['close']
    sma_50 = last_row['sma_50']
    sma_200 = last_row['sma_200']
    rsi = last_row['rsi_14']
    atr = last_row['atr_14']

    if pd.isna(sma_200) or pd.isna(atr):
        return 'hold', None, "Esperando datos suficientes..."

    # ==========================================
    # 1. GESTIÓN DE POSICIÓN ABIERTA (LONG)
    # ==========================================
    if current_position == 'long':
        if max_price is None or current_price > max_price:
            max_price = current_price
        
        trailing_stop = max_price - (1.5 * atr)

        if current_price <= trailing_stop:
            return 'reverse_to_short', current_price, f"Trailing Stop en {trailing_stop:.2f}. Asegurando ganancia y revirtiendo a SHORT"

    # ==========================================
    # 2. GESTIÓN DE POSICIÓN ABIERTA (SHORT)
    # ==========================================
    elif current_position == 'short':
        if min_price is None or current_price < min_price:
            min_price = current_price
            
        trailing_stop = min_price + (1.5 * atr)

        if current_price >= trailing_stop:
            return 'reverse_to_long', current_price, f"Trailing Stop en {trailing_stop:.2f}. Asegurando ganancia y revirtiendo a LONG"

    # ==========================================
    # 3. APERTURA DE NUEVA POSICIÓN (Si no hay nada abierto)
    # ==========================================
    else:
        # FILTRO ANTI-LATERAL
        fuerza_tendencia = abs(sma_50 - sma_200) / current_price
        
        if fuerza_tendencia < 0.002:
            return 'hold', None, "Mercado lateral detectado. No se abren operaciones (evitando comisiones)."
            
        # Filtro de tendencia macro y RSI
        if sma_50 > sma_200 and rsi < 70:
            return 'buy', current_price, f"Tendencia alcista fuerte. Abriendo LONG en {current_price}"
        elif sma_50 < sma_200 and rsi > 30:
            return 'sell', current_price, f"Tendencia bajista fuerte. Abriendo SHORT en {current_price}"

    return 'hold', None, "Sin señales claras. Esperando..."