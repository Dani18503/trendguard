#!/bin/bash

# ==========================================
# TrendGuard - Instalador Automático (Fase 8)
# ==========================================

echo "========================================="
echo "🚀 Iniciando instalación de TrendGuard..."
echo "========================================="

# 1. Actualizar el sistema
echo "📦 Actualizando paquetes del sistema..."
sudo apt-get update -y && sudo apt-get upgrade -y

# 2. Instalar Docker y Docker Compose si no están instalados
if ! command -v docker &> /dev/null; then
    echo "🐳 Instalando Docker..."
    sudo apt-get install -y docker.io docker-compose
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER
else
    echo "✅ Docker ya está instalado."
fi

# 3. Clonar el repositorio de TrendGuard
# (Asegúrate de tener el repo público o de configurar las credenciales)
if [ ! -d "trendguard" ]; then
    echo "📥 Descargando el código de TrendGuard..."
    git clone https://github.com/Dani18503/trendguard.git
    cd trendguard
else
    echo "✅ El repositorio ya existe. Entrando a la carpeta..."
    cd trendguard
    git pull origin main
fi

# 4. Configurar el archivo .env
if [ ! -f ".env" ]; then
    echo "⚙️ Creando archivo de configuración .env..."
    echo "BINANCE_API_KEY=tu_api_key_aqui" > .env
    echo "BINANCE_SECRET=tu_secret_aqui" >> .env
    echo "TELEGRAM_TOKEN=tu_token_aqui" >> .env
    echo "TELEGRAM_CHAT_ID=tu_chat_id_aqui" >> .env
    echo "⚠️ Por favor, edita el archivo .env con tus credenciales reales."
else
    echo "✅ El archivo .env ya existe."
fi

# 5. Colocar la licencia y la llave pública
if [ -f "../license.lic" ]; then
    cp ../license.lic .
    cp ../public_key.pem .
    echo "🔐 Licencia y llave pública copiadas."
else
    echo "⚠️ No se encontró el archivo license.lic. Asegúrate de colocarlo en la carpeta raíz."
fi

# 6. Levantar los contenedores
echo "🚀 Levantando el bot y el panel de TrendGuard..."
sudo docker-compose up -d --build

echo "========================================="
echo "✅ ¡Instalación completada con éxito!"
echo "El bot TrendGuard está corriendo en tu VPS."
echo "Puedes ver el panel en: http://TU_IP:8501"
echo "========================================="
