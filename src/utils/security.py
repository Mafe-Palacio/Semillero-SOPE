"""
Utilidades de seguridad para contraseñas.

Decisión de arquitectura: se usa bcrypt (hash_password / verify_password)
como único algoritmo de hasheo en todo el proyecto. Es el estándar de facto
para contraseñas: incluye salt automático por hash y su costo (rounds) se
puede ajustar según el hardware disponible sin cambiar de librería.
"""

import bcrypt
import secrets


def hash_password(plain: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica una contraseña en texto plano contra su hash bcrypt."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Valida requisitos mínimos de robustez antes de hashear la contraseña."""
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


def generar_codigo_otp() -> str:
    """Genera un código OTP numérico de 6 dígitos usando el generador
    criptográficamente seguro del módulo `secrets` (no `random`, que no
    es apto para nada relacionado con seguridad/autenticación)."""
    return f"{secrets.randbelow(1_000_000):06d}"
