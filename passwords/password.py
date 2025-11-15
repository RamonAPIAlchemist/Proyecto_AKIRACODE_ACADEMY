from flask import Flask
from flask_bcrypt import Bcrypt

inicio = Flask(__name__)
bcrypt = Bcrypt(inicio)

password_plano = "mi_contresa_secreta"
hash_password = bcrypt.generate_password_hash(password_plano).decode('utf-8')

print(f"Contraseña encriptada: {hash_password}")

# Para verificar la contraseña 
contraseña_interna = bcrypt.check_password_hash(hash_password, password_plano)
print(f"La contraseña es correcta: {contraseña_interna}")