import bcrypt
import hashlib
import secrets
from typing import Tuple


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


class PasswordManager:
    """Gestor de contraseñas con hash seguro"""

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
        )
        return f"{salt}:{password_hash.hex()}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            salt, hash_part = password_hash.split(":")
            password_hash_check = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
            )
            return password_hash_check.hex() == hash_part
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        if len(password) > 128:
            return False, "La contraseña no puede exceder 128 caracteres"
        if not any(c.isupper() for c in password):
            return False, "La contraseña debe contener al menos una letra mayúscula"
        if not any(c.islower() for c in password):
            return False, "La contraseña debe contener al menos una letra minúscula"
        if not any(c.isdigit() for c in password):
            return False, "La contraseña debe contener al menos un número"
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "La contraseña debe contener al menos un carácter especial"
        return True, "Contraseña válida"
