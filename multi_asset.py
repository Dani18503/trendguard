"""
TrendGuard - Multi Asset (Fase 7, Bloque 3)
Descarga velas reales de Binance y procesa cada activo independientemente.
"""

import time
import pandas as pd
from indicators import add_all_indicators
from strategy import generate_signal


DEFAULT_ASSETS = ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT"]


def symbol_to_ohlcv(symbol):
    """Convierte 'BTC/USDT:USDT' -> 'BTC/USDT' para fetch_ohlcv."""
    return symbol.split(":")[0] if ":" in symbol else symbol


def get_enabled_assets(config):
    assets_conf = config.get("assets", {})
    enabled = []
    for symbol, cfg in assets_conf.items():
        if isinstance(cfg, dict) and cfg.get("enabled", False):
            enabled.append(symbol)
    return enabled


def get_asset_state(state, symbol):
    asset = state.get(symbol, {})
    return {
        "current_position": asset.get("current_position"),
        "entry_price": asset.get("entry_price", 0.0),
        "max_price": asset.get("max_price", 0.0),
        "min_price": asset.get("min_price", 0.0),
        "cantidad": asset.get("cantidad", 0.0),
    }


def fetch_ohlcv_safe(exchange, symbol, timeframe="1d", limit=300, retries=3):
    """Descarga velas con reintentos. Retorna DataFrame o None."""
    ohlcv_symbol = symbol_to_ohlcv(symbol)
    for attempt in range(retries):
        try:
            raw = exchange.fetch_ohlcv(ohlcv_symbol, timeframe=timeframe, limit=limit)
            if not raw or len(raw) < 200:
                return None
            df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
            return df
        except Exception as e:
            print(f"  [!] Error fetch {ohlcv_symbol} (intento {attempt+1}): {e}")
            time.sleep(2)
    return None


def process_asset_from_df(symbol, df, state):
    asset_state = get_asset_state(state, symbol)
    df = add_all_indicators(df)
    signal, price, mensaje = generate_signal(
        df,
        current_position=asset_state["current_position"],
        entry_price=asset_state["entry_price"],
        max_price=asset_state["max_price"],
        min_price=asset_state["min_price"],
    )
    if price is None:
        price = float(df['close'].iloc[-1])
    return {
        "symbol": symbol,
        "signal": signal,
        "price": price,
        "mensaje": mensaje,
        "position": asset_state["current_position"],
    }


def fetch_all_assets(exchange, config, timeframe="1d", limit=300):
    """Descarga velas para todos los activos habilitados. Retorna dict."""
    enabled = get_enabled_assets(config)
    dataframes = {}
    for symbol in enabled:
        df = fetch_ohlcv_safe(exchange, symbol, timeframe, limit)
        if df is not None:
            dataframes[symbol] = df
    return dataframes


def process_all_assets(dataframes, state, config):
    enabled = get_enabled_assets(config)
    results = {}
    for symbol in enabled:
        try:
            if symbol not in dataframes:
                results[symbol] = {
                    "symbol": symbol, "signal": "skip",
                    "mensaje": "Sin datos", "price": None, "position": None,
                }
                continue
            results[symbol] = process_asset_from_df(symbol, dataframes[symbol], state)
        except Exception as e:
            results[symbol] = {
                "symbol": symbol, "signal": "error",
                "mensaje": str(e), "price": None, "position": None,
            }
    return results


# ============================================================
# BLOQUE 3.3: MIGRACION DE STATE A MULTI-ACTIVO
# ============================================================

def migrate_state_to_multi(state, config, default_symbol="BTC/USDT:USDT"):
    """
    Migra state.json viejo (flat) al nuevo formato multi-activo.
    Si ya esta migrado, no hace nada.
    """
    # Detectar si ya esta migrado
    if "current_position" not in state:
        # Ya esta en formato multi-activo
        return state, False

    # Estructura vieja detectada -> migrar
    migrated = {}
    migrated[default_symbol] = {
        "current_position": state.get("current_position"),
        "entry_price": state.get("entry_price", 0.0),
        "max_price": state.get("max_price", 0.0),
        "min_price": state.get("min_price", 0.0),
        "cantidad": state.get("cantidad", 0.0),
    }

    # Inicializar los demas activos habilitados
    for symbol in get_enabled_assets(config):
        if symbol not in migrated:
            migrated[symbol] = {
                "current_position": None,
                "entry_price": 0.0,
                "max_price": 0.0,
                "min_price": 0.0,
                "cantidad": 0.0,
            }

    # Preservar drawdown si existe
    if "drawdown" in state:
        migrated["drawdown"] = state["drawdown"]

    return migrated, True
