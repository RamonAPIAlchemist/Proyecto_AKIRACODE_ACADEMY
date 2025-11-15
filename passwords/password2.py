#werkzeug
from werkzeug.security import generate_password_hash, check_password_hash

texto = "x?_P-M.4!el"

texto_encryptado = generate_password_hash(texto)

print(f"texto encryptado: {texto_encryptado}")

print(f" el texto es correcto: {check_password_hash(texto_encryptado, texto)}")