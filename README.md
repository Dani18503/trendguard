# TrendGuard

Bot de trading automatizado para Binance Futures con seguimiento de tendencia,
gestion de riesgo y notificaciones a Telegram.

## Caracteristicas

- Seguimiento de tendencia con cruce de EMAs y filtro RSI
- Trailing stop configurable para asegurar ganancias
- Gestion de riesgo: 1% del balance por operacion
- Stop loss obligatorio en cada trade
- Notificaciones a Telegram en tiempo real
- Modos Simple (principiantes) y Pro (avanzados)

## Requisitos

- Python 3.11+
- Cuenta en Binance Futures (Testnet o Real)
- Bot de Telegram + canal privado

## Instalacion

1. Clonar el repositorio:
   git clone <url-del-repo>
   cd trendguard

2. Crear entorno virtual:
   python3 -m venv venv
   source venv/bin/activate

3. Instalar dependencias:
   pip install -r requirements.txt

4. Copiar el archivo de ejemplo y rellenar credenciales:
   cp .env.example .env
   nano .env

5. Ejecutar:
   python bot.py

## Estructura del proyecto

- bot.py: Entrypoint principal
- config.py: Carga de configuracion desde .env
- notifier.py: Notificaciones a Telegram
- exchange.py: Conexion con Binance Futures
- strategy.py: Logica de estrategia de trading
- risk.py: Gestion de riesgo y trailing stop

## Descargo de responsabilidad

El trading con apalancamiento conlleva alto riesgo. Usa bajo tu propio riesgo.
