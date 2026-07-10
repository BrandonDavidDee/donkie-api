"""
This logic only exists here for testing and reference. This entire operation should not take place within this project.

NoEncryption() on the private key — for dev only, but in production encrypt the private key at rest with a passphrase

The purpose of base64 encoding is for storing a multi line private_pem key as an env file which is one line.
"""
import base64

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

# 1. Generate the private key — this stays on the consuming app's server, forever.
private_key = ec.generate_private_key(ec.SECP256R1())

# 2. Derive the public key — this is what gets sent to the chat service for storage (app_keys.public_key).
public_key = private_key.public_key()

# 3. Serialize both to PEM format (standard, portable text format)
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()  # see docstring
)

public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

private_encoded_key = base64.b64encode(private_pem).decode()
print(private_encoded_key)
# ^^ store this as an env variable in the consuming application.

print('-----')

print(public_pem.decode())
# this is what gets stored in app_keys.public_key
