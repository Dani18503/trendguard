import os

# Ruta al archivo del bot
BOT_FILE = '/home/ubuntu/trendguard/bot_multi.py'

# Leer el archivo
with open(BOT_FILE, 'r') as f:
    lines = f.readlines()

new_lines = []
license_code_injected = False

# Recorrer las líneas buscando el punto de anclaje
for line in lines:
    new_lines.append(line)
    
    # Insertamos el código justo después de cargar el .env
    if "load_dotenv('/home/ubuntu/trendguard/.env')" in line:
        new_lines.append("\n# --- VERIFICACIÓN DE LICENCIA (FASE 8) ---\n")
        new_lines.append("from licensing import validate_license\n")
        new_lines.append("if not validate_license(license_file='/home/ubuntu/trendguard/license.lic', public_key_path='/home/ubuntu/trendguard/public_key.pem'):\n")
        new_lines.append("    print('🚫 LICENCIA INVÁLIDA O EXPIRADA. EL BOT NO ARRANCARÁ.')\n")
        new_lines.append("    exit(1)\n")
        new_lines.append("# -----------------------------------------\n")
        license_code_injected = True

# Guardar el archivo modificado
if license_code_injected:
    with open(BOT_FILE, 'w') as f:
        f.writelines(new_lines)
    print("✅ Inyección completada exitosamente.")
else:
    print("❌ No se encontró el punto de anclaje. No se modificó el archivo.")
