"""
TrendGuard - Modulo de configuracion
Carga variables desde .env y las expone de forma tipada.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar el .env desde la raiz del proyecto
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


def _get_env(key: str, default=None, required: bool = False) -> str:
    """Lee una variable de entorno, con manejo de errores."""
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"Falta la variable obligatoria en .env: {key}")
    return value


# --- Binance ---
BINANCE_API_KEY = _get_env("BINANCE_API_KEY", default="")
BINANCE_API_SECRET = _get_env("BINANCE_API_SECRET", default="")
BINANCE_TESTNET = _get_env("BINANCE_TESTNET", default="true").lower() == "true"

# --- Telegram ---
TELEGRAM_BOT_TOKEN = _get_env("TELEGRAM_BOT_TOKEN", required=True)
TELEGRAM_CHAT_ID = _get_env("TELEGRAM_CHAT_ID", required=True)

# --- Trading ---
SYMBOL = _get_env("SYMBOL", default="BTC/USDT:USDT")
LEVERAGE = int(_get_env("LEVERAGE", default="3"))
RISK_PER_TRADE = float(_get_env("RISK_PER_TRADE", default="0.01"))
TIMEFRAME = _get_env("TIMEFRAME", default="15m")

# --- Modo ---
MODE = _get_env("MODE", default="simple").lower()

# --- Trailing Stop ---
TRAILING_TRIGGER_PCT = float(_get_env("TRAILING_TRIGGER_PCT", default="1.0"))
TRAILING_DISTANCE_PCT = float(_get_env("TRAILING_DISTANCE_PCT", default="0.5"))

# --- Logging ---
LOG_LEVEL = _get_env("LOG_LEVEL", default="INFO").upper()


if __name__ == "__main__":
    print("=== Configuracion TrendGuard ===")
    print(f"Symbol:          {SYMBOL}")
    print(f"Timeframe:       {TIMEFRAME}")
    print(f"Leverage:        {LEVERAGE}x")
    print(f"Risk per trade:  {RISK_PER_TRADE * 100}%")
    print(f"Mode:            {MODE}")
    print(f"Testnet:         {BINANCE_TESTNET}")
    print(f"Telegram Chat:   {TELEGRAM_CHAT_ID}")
    print(f"Token cargado:   {'SI' if TELEGRAM_BOT_TOKEN else 'NO'}")
