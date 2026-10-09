"""
TrendGuard - Multi Asset (Fase 7, Bloque 3)
Itera sobre BTC, ETH, SOL procesando cada uno independientemente.
NO envia ordenes. NO conecta a Binance por si solo.
"""

import pandas as pd
from indicators import add_all_indicators
from strategy import generate_signal


DEFAULT_ASSETS = ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT"]


def get_enabled_assets(config):
    """Retorna lista de simbolos activos desde runtime_config.json."""
    assets_conf = config.get("assets", {})
    enabled = []
    for symbol, cfg in assets_conf.items():
        if isinstance(cfg, dict) and cfg.get("enabled", False):
            enabled.append(symbol)
    return enabled


def get_asset_state(state, symbol):
    """Extrae el estado de un activo. Si no existe, retorna default vacio."""
    asset = state.get(symbol, {})
    return {
        "current_position": asset.get("current_position"),
        "entry_price": asset.get("entry_price", 0.0),
        "max_price": asset.get("max_price", 0.0),
        "min_price": asset.get("min_price", 0.0),
        "cantidad": asset.get("cantidad", 0.0),
    }


def process_asset_from_df(symbol, df, state):
    """
    Procesa un activo dado un DataFrame ya cargado.
    Retorna dict con signal, price, mensaje, posicion.
    """
    asset_state = get_asset_state(state, symbol)

    df = add_all_indicators(df)

    signal, price, mensaje = generate_signal(
        df,
        current_position=asset_state["current_position"],
        entry_price=asset_state["entry_price"],
        max_price=asset_state["max_price"],
        min_price=asset_state["min_price"],
    )

    # FIX: garantizar price nunca None (bug reportes Telegram)
    if price is None:
        price = float(df['close'].iloc[-1])

    return {
        "symbol": symbol,
        "signal": signal,
        "price": price,
        "mensaje": mensaje,
        "position": asset_state["current_position"],
    }


def process_all_assets(dataframes, state, config):
    """
    Procesa todos los activos habilitados.
    dataframes: dict {symbol: df}
    """
    enabled = get_enabled_assets(config)
    results = {}

    for symbol in enabled:
        try:
            if symbol not in dataframes:
                results[symbol] = {
                    "symbol": symbol, "signal": "skip",
                    "mensaje": "Sin datos", "price": None,
                }
                continue
            results[symbol] = process_asset_from_df(
                symbol, dataframes[symbol], state
            )
        except Exception as e:
            results[symbol] = {
                "symbol": symbol, "signal": "error",
                "mensaje": str(e), "price": None,
            }

    return results
