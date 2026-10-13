from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Generar el par de llaves
private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# Guardar la llave privada (SECRETA - Nunca se comparte)
with open("private_key.pem", "wb") as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))

# Guardar la llave pública (PÚBLICA - Va en el código del bot)
with open("public_key.pem", "wb") as f:
    f.write(public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

print("¡Llaves generadas con éxito!")
