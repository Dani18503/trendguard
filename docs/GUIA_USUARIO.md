# 🚀 TrendGuard - Guía de Usuario

¡Bienvenido a TrendGuard! Este bot multi-activo (BTC/ETH/SOL) opera por ti con gestión de riesgo profesional.

## 📋 Requisitos
- Un VPS (Ubuntu 22.04 o superior) con al menos 1GB de RAM.
- Cuenta en Binance con API Key y Secret.
- Un bot de Telegram con Token y Chat ID.

## 🛠️ Instalación (1 solo comando)
Una vez que tengas tu VPS, conéctate por SSH y ejecuta:

bash install.sh

El instalador hará todo el trabajo: instalará Docker, descargará el código y configurará el entorno.

## ⚙️ Configuración
Edita el archivo .env con tus credenciales:

nano .env

Rellena:
- BINANCE_API_KEY: Tu API Key de Binance.
- BINANCE_SECRET: Tu Secret de Binance.
- TELEGRAM_TOKEN: El token de tu bot de Telegram.
- TELEGRAM_CHAT_ID: Tu ID de chat de Telegram.

## 🔐 Activación de Licencia
Coloca el archivo license.lic y public_key.pem en la carpeta raíz del proyecto. El bot verificará la licencia automáticamente al arrancar.

## 🚀 Arrancar el Bot
sudo docker-compose up -d

## 📊 Panel de Control
Accede al panel en: http://TU_IP:8501

## ❓ Preguntas Frecuentes
- ¿El bot opera solo? Sí, una vez configurado, opera 24/7.
- ¿Qué pasa si se vence la licencia? El bot se detiene. Contacta a soporte para renovar.
- ¿Puedo cambiar los activos? Sí, en el archivo runtime_config.json.

---
© 2026 TrendGuard. Todos los derechos reservados.
