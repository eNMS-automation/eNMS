# Fernet AES CBC

from cryptography.fernet import Fernet

key = Fernet.generate_key()
fernet = Fernet(key)
token = fernet.encrypt(b"bytes data")
decrypted = fernet.decrypt(token)
