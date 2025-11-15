# crypto_utils.py
from cryptography.fernet import Fernet

# Clave para cifrado (debes guardarla de forma segura)
# Para generar una nueva clave: 
# from cryptography.fernet import Fernet
# clave = Fernet.generate_key()
# print(clave.decode())

CLAVE = b'tu_clave_generada_aqui'  # Reemplaza con tu clave real

def cifrar_contraseña(password):
    """Cifra una contraseña"""
    try:
        fernet = Fernet(CLAVE)
        return fernet.encrypt(password.encode()).decode()
    except Exception as e:
        print(f"Error cifrando: {e}")
        return password  # Si hay error, devuelve la original

def descifrar_contraseña(password_cifrada):
    """Descifra una contraseña (solo para mostrar en admin)"""
    try:
        fernet = Fernet(CLAVE)
        return fernet.decrypt(password_cifrada.encode()).decode()
    except:
        return password_cifrada  # Si no se puede descifrar, devuelve la original

def verificar_contraseña(password_plana, password_cifrada):
    """Verifica si una contraseña en texto plano coincide con la cifrada"""
    try:
        contraseña_descifrada = descifrar_contraseña(password_cifrada)
        return contraseña_descifrada == password_plana
    except:
        # Si hay error en descifrado, compara directamente (para migración)
        return password_plana == password_cifrada