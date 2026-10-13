import json
import base64
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

def load_public_key(path):
    with open(path, "rb") as f:
        return serialization.load_pem_public_key(f.read())

def validate_license(license_file="license.lic", public_key_path="public_key.pem"):
    # 1. Cargar la llave pública
    public_key = load_public_key(public_key_path)

    # 2. Leer el archivo de licencia
    with open(license_file, "r") as f:
        license_data = json.load(f)

    payload = license_data["payload"]
    signature = base64.b64decode(license_data["signature"])

    # 3. Reconstruir los datos para verificar la firma
    payload_json = json.dumps(payload, sort_keys=True).encode('utf-8')

    # 4. Verificar la firma digital
    try:
        public_key.verify(signature, payload_json)
    except Exception:
        print("❌ ERROR: La licencia es inválida o ha sido modificada.")
        return False

    # 5. Verificar la fecha de expiración
    exp_date = datetime.fromisoformat(payload["expiration_date"])
    if datetime.now() > exp_date:
        print(f"❌ ERROR: La licencia expiró el {exp_date}")
        return False

    # 6. Si todo está bien, mostrar los datos del cliente
    print("✅ Licencia válida.")
    print(f"Cliente: {payload['customer_id']}")
    print(f"Expira: {exp_date}")
    print(f"Activos permitidos: {payload['assets_allowed']}")
    return True
