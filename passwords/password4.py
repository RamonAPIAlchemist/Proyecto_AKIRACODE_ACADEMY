from cryptography.fernet import Fernet


texto = "x?_P-M.4!el"



#generar una clave  y crear un objeto fernet

clave = Fernet.generate_key()
objeto = Fernet(clave)

texto_encriptado = objeto.encrypt(texto.encode())

print(f"texto encryptado: {texto_encriptado}")

texto_desencriptado = objeto.decrypt(texto_encriptado).decode()

print(f" el texto desencriptado: {texto_desencriptado}")