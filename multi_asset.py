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


# ============================================================
# BLOQUE 4: CORRELACION ENTRE ACTIVOS
# ============================================================

from risk_manager import calculate_correlation, get_correlation_action


def get_open_symbols(state):
    """Retorna lista de simbolos con posicion abierta."""
    open_syms = []
    for key, val in state.items():
        if key in ("drawdown", "correlation"):
            continue
        if isinstance(val, dict) and val.get("current_position"):
            open_syms.append(key)
    return open_syms


def check_correlation_for_signal(symbol, dataframes, state, config):
    """
    Determina si una senal de entrada debe bloquearse o reducir riesgo por correlacion.

    Returns:
        dict con: action ('block'|'half_risk'|'normal'), max_corr (float),
                  correlated_with (str|None)
    """
    corr_conf = config.get("correlation", {})
    block_thresh = corr_conf.get("block_threshold", 0.85)
    half_thresh = corr_conf.get("half_risk_threshold", 0.70)
    window = corr_conf.get("window_days", 30)

    open_syms = get_open_symbols(state)

    # Sin posiciones abiertas -> normal
    if not open_syms:
        return {"action": "normal", "max_corr": 0.0, "correlated_with": None}

    # Sin datos del activo nuevo -> no se puede calcular
    if symbol not in dataframes:
        return {"action": "normal", "max_corr": 0.0, "correlated_with": None}

    df_new = dataframes[symbol]
    if len(df_new) < window + 1:
        return {"action": "normal", "max_corr": 0.0, "correlated_with": None}

    returns_new = df_new['close'].pct_change().dropna()

    max_corr = 0.0
    worst_symbol = None

    for other in open_syms:
        if other == symbol:
            continue
        if other not in dataframes:
            continue
        df_other = dataframes[other]
        if len(df_other) < window + 1:
            continue

        returns_other = df_other['close'].pct_change().dropna()

        # Alinear por indice comun
        aligned = pd.concat([returns_new, returns_other], axis=1, join='inner')
        if len(aligned) < 2:
            continue

        corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
        if corr is None or pd.isna(corr):
            continue

        if corr > max_corr:
            max_corr = float(corr)
            worst_symbol = other

    action = get_correlation_action(max_corr, block_thresh, half_thresh)
    return {"action": action, "max_corr": max_corr, "correlated_with": worst_symbol}


def apply_correlation_filter(symbol, signal, dataframes, state, config):
    """
    Aplica filtro de correlacion a una senal de entrada.
    Solo afecta a senales 'buy' (nuevas entradas).

    Returns:
        dict con: allowed (bool), adjusted_signal (str), reason (str)
    """
    if signal != 'buy':
        return {"allowed": True, "adjusted_signal": signal, "reason": "no es entrada"}

    corr_result = check_correlation_for_signal(symbol, dataframes, state, config)
    action = corr_result["action"]

    if action == "block":
        return {
            "allowed": False,
            "adjusted_signal": "hold",
            "reason": f"correlacion {corr_result['max_corr']:.3f} con {corr_result['correlated_with']} > 0.85 (BLOQUEADO)",
            "corr": corr_result["max_corr"],
            "with": corr_result["correlated_with"],
        }
    elif action == "half_risk":
        return {
            "allowed": True,
            "adjusted_signal": "buy",
            "reason": f"correlacion {corr_result['max_corr']:.3f} con {corr_result['correlated_with']} -> HALF RISK",
            "corr": corr_result["max_corr"],
            "with": corr_result["correlated_with"],
            "half_risk": True,
        }
    else:
        return {
            "allowed": True,
            "adjusted_signal": "buy",
            "reason": "correlacion baja, riesgo normal",
            "corr": corr_result["max_corr"],
            "with": corr_result["correlated_with"],
        }
