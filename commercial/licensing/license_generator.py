import json
import base64
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

def load_private_key(path):
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def generate_license(customer_id, expiration_days=30, assets=None):
    if assets is None:
        assets = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

    exp_date = (datetime.now() + timedelta(days=expiration_days)).isoformat()

    payload = {
        "customer_id": customer_id,
        "expiration_date": exp_date,
        "assets_allowed": assets,
        "issued_at": datetime.now().isoformat()
    }

    payload_json = json.dumps(payload, sort_keys=True).encode('utf-8')
    private_key = load_private_key("private_key.pem")
    signature = private_key.sign(payload_json)

    license_data = {
        "payload": payload,
        "signature": base64.b64encode(signature).decode('utf-8')
    }

    filename = f"license_{customer_id}.lic"
    with open(filename, "w") as f:
        json.dump(license_data, f, indent=4)

    print(f"✅ Licencia generada: {filename}")
    print(f"Cliente: {customer_id}")
    print(f"Expira: {exp_date}")
    print(f"Activos: {assets}")

generate_license("Cliente_Prueba", expiration_days=30)
