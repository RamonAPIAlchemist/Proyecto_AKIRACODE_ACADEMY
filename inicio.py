from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import os
import time
from werkzeug.utils import secure_filename
import MySQLdb.cursors
from datetime import datetime
import bcrypt
import re

# Inicializamos la aplicación Flask
app = Flask(__name__, template_folder="Templates")
app.secret_key = '09f78ead-8a13-11f0-9f04-089798bc6dda'

# ----------------- CONEXIÓN A MYSQL -----------------
app.config['MYSQL_HOST'] = 'bnxoi9nhopkfowd6q4mn-mysql.services.clever-cloud.com'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'ukcbxspsvbqbrdqa'
app.config['MYSQL_PASSWORD'] = 'YW6fvimifkgJjJz5IWBT'
app.config['MYSQL_DB'] = 'bnxoi9nhopkfowd6q4mn'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Configuración para uploads de imágenes
UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

mysql = MySQL(app)

# ----------------- FUNCIONES DE CIFRADO MEJORADAS -----------------
def hash_password(password):
    """Convierte una contraseña en texto plano a hash bcrypt"""
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"Error al hashear contraseña: {e}")
        return None

def check_password(plain_password, hashed_password):
    """Verifica si una contraseña en texto plano coincide con el hash"""
    try:
        if not hashed_password:
            return False
        
        # Verificar si el hash parece ser un hash bcrypt válido
        if not hashed_password.startswith('$2b$'):
            # Si no es un hash bcrypt, comparar directamente (para migración)
            return plain_password == hashed_password
        
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"Error al verificar contraseña: {e}")
        return False

def is_bcrypt_hash(password):
    """Verifica si una cadena parece ser un hash bcrypt"""
    return password.startswith('$2b$') and len(password) == 60

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------- RUTAS -----------------

@app.route('/')
def inicio():
    return render_template("index.html")

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    user = {'nombre': '', 'email': '', 'mensaje': ''}
    if request.method == 'GET':
        user['nombre'] = request.args.get('nombre', '')
        user['email'] = request.args.get('email', '')
        user['mensaje'] = request.args.get('mensaje', '')
    return render_template("contacto.html", usuario=user)

@app.route('/contactopost', methods=['GET', 'POST'])
def contactopost():
    user = {'nombre': '', 'email': '', 'mensaje': ''}
    if request.method == 'POST':
        user['nombre'] = request.form.get('nombre', '')
        user['email'] = request.form.get('email', '')
        user['mensaje'] = request.form.get('mensaje', '')
    return render_template("contactopost.html", usuario=user)

# ----------------- LOGIN MEJORADO -----------------
@app.route('/login', methods=['GET'])
def login():
    return render_template("login.html")

@app.route('/accesologin', methods=['POST'])
def accesologin():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        flash('Por favor ingrese email y contraseña', 'error')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM usuario WHERE email=%s", (email,))
        user = cur.fetchone()
        
        if user and check_password(password, user['password']):
            # Si la contraseña es correcta y está en texto plano, migrarla a bcrypt
            if not is_bcrypt_hash(user['password']):
                hashed_password = hash_password(password)
                if hashed_password:
                    cur.execute("UPDATE usuario SET password = %s WHERE id = %s", 
                               (hashed_password, user['id']))
                    mysql.connection.commit()
            
            # Actualizar último acceso
            cur.execute("UPDATE usuario SET ultimo_acceso = NOW() WHERE id = %s", (user['id'],))
            mysql.connection.commit()
            
            session['usuario'] = user['email']
            session['nombre'] = user['nombre']
            session['rol'] = user['id_rol']
            session['id'] = user['id']
            session['email'] = user['email']
            
            # Cargar fechas si existen
            if user.get('fecha_creacion'):
                session['fecha_creacion'] = user['fecha_creacion'].strftime('%d/%m/%Y %H:%M')
            if user.get('ultimo_acceso'):
                session['ultimo_acceso'] = user['ultimo_acceso'].strftime('%d/%m/%Y %H:%M')
            
            # Cargar foto de perfil si existe
            if user.get('foto_perfil'):
                session['foto_perfil'] = user['foto_perfil']
            else:
                session['foto_perfil'] = 'img/user.png'

            cur.close()
            
            if user['id_rol'] == 1:
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('inicio'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
            return redirect(url_for('login'))
            
    except Exception as e:
        flash('Error en el servidor. Por favor intente más tarde.', 'error')
        print(f"Error en login: {e}")
        return redirect(url_for('login'))
    finally:
        cur.close()

# ----------------- REGISTRO -----------------
@app.route('/Registro', methods=['GET', 'POST'])
def Registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        id_rol = 2

        if not nombre or not email or not password:
            flash('Por favor complete todos los campos', 'error')
            return render_template("Registro.html")

        # Verificar si el email ya existe
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM usuario WHERE email = %s", (email,))
        if cur.fetchone():
            flash('El email ya está registrado', 'error')
            cur.close()
            return render_template("Registro.html")

        # Cifrar la contraseña
        hashed_password = hash_password(password)
        if not hashed_password:
            flash('Error al crear la cuenta. Por favor intente nuevamente.', 'error')
            cur.close()
            return render_template("Registro.html")

        cur.execute("INSERT INTO usuario (email, nombre, password, id_rol, fecha_creacion, ultimo_acceso) VALUES (%s, %s, %s, %s, NOW(), NOW())",
                    (email, nombre, hashed_password, id_rol))
        mysql.connection.commit()
        cur.close()

        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template("Registro.html")

# ----------------- PÁGINA DE USUARIO -----------------
@app.route('/usuario')
def usuario():
    if 'usuario' in session:
        return render_template("usuario.html", usuario=session['usuario'])
    else:
        return redirect(url_for('login'))

# ----------------- RUTA DEL ADMIN -----------------
@app.route('/admin')
def admin():
    if 'usuario' in session and session.get('rol') == 1:
        return render_template("admin.html", usuario=session['usuario'])
    else:
        flash('Acceso denegado', 'error')
        return redirect(url_for('login'))

# ----------------- PERFIL DE USUARIO -----------------
@app.route('/listar', methods=['GET', 'POST'])
def listar():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    # ----------------- AGREGAR USUARIO -----------------
    if request.method == 'POST' and 'agregar_usuario' in request.form:
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        id_rol = request.form.get('id_rol', 2)

        # Verificar si el email ya existe
        cur.execute("SELECT id FROM usuario WHERE email = %s", (email,))
        if cur.fetchone():
            flash('El email ya está registrado', 'error')
            cur.close()
            return redirect(url_for('listar'))

        # Cifrar la contraseña
        hashed_password = hash_password(password)
        if hashed_password:
            cur.execute("INSERT INTO usuario (nombre, email, password, id_rol, fecha_creacion, ultimo_acceso) VALUES (%s, %s, %s, %s, NOW(), NOW())",
                        (nombre, email, hashed_password, id_rol))
            mysql.connection.commit()
            flash("Usuario agregado correctamente!", "success")
        else:
            flash("Error al crear el usuario", "error")

        return redirect(url_for('listar'))

    # ----------------- EDITAR USUARIO -----------------
    elif request.method == 'POST' and 'editar_usuario' in request.form:
        user_id = request.form['id']
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        id_rol = request.form.get('id_rol', 2)
        
        # Manejar el campo último_acceso
        ultimo_acceso_str = request.form.get('ultimo_acceso', '')
        
        ultimo_acceso = None
        if ultimo_acceso_str:
            try:
                ultimo_acceso = datetime.strptime(ultimo_acceso_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Formato de fecha y hora inválido', 'error')
                return redirect(url_for('listar'))

        # Si se proporcionó una nueva contraseña, cifrarla
        if password:
            hashed_password = hash_password(password)
            if hashed_password:
                if ultimo_acceso:
                    cur.execute("""
                        UPDATE usuario 
                        SET nombre=%s, email=%s, password=%s, id_rol=%s, ultimo_acceso=%s, fecha_actualizacion=NOW() 
                        WHERE id=%s
                    """, (nombre, email, hashed_password, id_rol, ultimo_acceso, user_id))
                else:
                    cur.execute("""
                        UPDATE usuario 
                        SET nombre=%s, email=%s, password=%s, id_rol=%s, fecha_actualizacion=NOW() 
                        WHERE id=%s
                    """, (nombre, email, hashed_password, id_rol, user_id))
            else:
                flash("Error al actualizar la contraseña", "error")
                return redirect(url_for('listar'))
        else:
            # Si no se cambió la contraseña, mantener la actual
            if ultimo_acceso:
                cur.execute("""
                    UPDATE usuario 
                    SET nombre=%s, email=%s, id_rol=%s, ultimo_acceso=%s, fecha_actualizacion=NOW() 
                    WHERE id=%s
                """, (nombre, email, id_rol, ultimo_acceso, user_id))
            else:
                cur.execute("""
                    UPDATE usuario 
                    SET nombre=%s, email=%s, id_rol=%s, fecha_actualizacion=NOW() 
                    WHERE id=%s
                """, (nombre, email, id_rol, user_id))
            
        mysql.connection.commit()
        flash("Usuario actualizado correctamente!", "success")
        return redirect(url_for('listar'))

    # ----------------- ELIMINAR USUARIO -----------------
    if request.args.get('eliminar_usuario'):
        user_id = request.args.get('eliminar_usuario')
        # No permitir eliminarse a sí mismo
        if int(user_id) == session['id']:
            flash("No puedes eliminarte a ti mismo", "error")
        else:
            cur.execute("DELETE FROM usuario WHERE id = %s", (user_id,))
            mysql.connection.commit()
            flash("Usuario eliminado correctamente!", "danger")
        return redirect(url_for('listar'))

    # ----------------- OBTENER USUARIOS -----------------
    cur.execute("""
        SELECT *, 
               DATE_FORMAT(fecha_creacion, '%d/%m/%Y %H:%i') as fecha_creacion_formateada, 
               DATE_FORMAT(ultimo_acceso, '%d/%m/%Y %H:%i') as ultimo_acceso_formateada 
        FROM usuario
    """)
    usuarios = cur.fetchall()
    cur.close()

    return render_template("editar_usuario.html",
                           usuario=session['usuario'],
                           usuarios=usuarios)

# ----------------- RUTAS PARA EL PERFIL -----------------

@app.route('/cambiar_foto_perfil', methods=['POST'])
def cambiar_foto_perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        # Procesar foto predefinida
        foto_predefinida = request.form.get('foto_predefinida')
        if foto_predefinida:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE usuario SET foto_perfil = %s, fecha_actualizacion = NOW() WHERE id = %s", 
                       (foto_predefinida, session['id']))
            mysql.connection.commit()
            session['foto_perfil'] = foto_predefinida
            cur.close()
            flash('Foto de perfil actualizada correctamente', 'success')
            return redirect(url_for('listar'))
        
        # Procesar foto subida
        file = request.files.get('foto')
        if file and file.filename:
            if allowed_file(file.filename):
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"user_{session['id']}_{int(time.time())}.{file_extension}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                file.save(filepath)
                
                db_filepath = f"img/{unique_filename}"
                
                cur = mysql.connection.cursor()
                cur.execute("UPDATE usuario SET foto_perfil = %s, fecha_actualizacion = NOW() WHERE id = %s", 
                           (db_filepath, session['id']))
                mysql.connection.commit()
                cur.close()
                
                session['foto_perfil'] = db_filepath
                flash('Foto de perfil actualizada correctamente', 'success')
            else:
                flash('Formato de archivo no permitido. Use: PNG, JPG, JPEG, GIF', 'error')
        else:
            flash('No se seleccionó ningún archivo', 'error')
            
    except Exception as e:
        flash(f'Error al actualizar la foto: {str(e)}', 'error')
    
    return redirect(url_for('listar'))

@app.route('/actualizar_perfil', methods=['POST'])
def actualizar_perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        nombre = request.form['nombre']
        email = request.form['email']
        
        # Verificar si el email ya existe (excluyendo el usuario actual)
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM usuario WHERE email = %s AND id != %s", (email, session['id']))
        if cur.fetchone():
            flash('El email ya está en uso por otro usuario', 'error')
            cur.close()
            return redirect(url_for('listar'))
        
        cur.execute("UPDATE usuario SET nombre = %s, email = %s, fecha_actualizacion = NOW() WHERE id = %s", 
                   (nombre, email, session['id']))
        mysql.connection.commit()
        
        session['nombre'] = nombre
        session['email'] = email
        session['usuario'] = email
        
        flash('Perfil actualizado correctamente', 'success')
        cur.close()
        
    except Exception as e:
        flash(f'Error al actualizar el perfil: {str(e)}', 'error')
    
    return redirect(url_for('listar'))

@app.route('/cambiar_password', methods=['POST'])
def cambiar_password():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        password_actual = request.form['password_actual']
        nueva_password = request.form['nueva_password']
        confirmar_password = request.form['confirmar_password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM usuario WHERE id = %s", (session['id'],))
        usuario = cur.fetchone()
        
        if usuario and check_password(password_actual, usuario['password']):
            if nueva_password == confirmar_password:
                hashed_password = hash_password(nueva_password)
                if hashed_password:
                    cur.execute("UPDATE usuario SET password = %s, fecha_actualizacion = NOW() WHERE id = %s", 
                               (hashed_password, session['id']))
                    mysql.connection.commit()
                    flash('Contraseña actualizada correctamente', 'success')
                else:
                    flash('Error al actualizar la contraseña', 'error')
            else:
                flash('Las contraseñas nuevas no coinciden', 'error')
        else:
            flash('Contraseña actual incorrecta', 'error')
        
        cur.close()
        
    except Exception as e:
        flash(f'Error al cambiar la contraseña: {str(e)}', 'error')
    
    return redirect(url_for('listar'))

# ----------------- PRODUCTOS -----------------

@app.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = float(request.form['precio'])
        descripcion = request.form['descripcion']
        fecha = request.form.get('fecha')

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO productos (nombre, precio, descripcion, fecha)
            VALUES (%s, %s, %s, %s)
        """, (nombre, precio, descripcion, fecha))
        mysql.connection.commit()
        cur.close()

        flash('Curso agregado correctamente!', 'success')
        return redirect(url_for('agregar_producto'))

    return render_template('Agregar_productos.html', productos=productos)

@app.route('/eliminar_producto/<int:id>')
def eliminar_producto(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM productos WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    flash('Producto eliminado correctamente!', 'success')
    return redirect(url_for('agregar_producto'))

# RUTA FALTANTE - AGREGAR ESTA RUTA
@app.route('/listar_productos_agregados')
def listar_productos_agregados():
    """Redirige a la página de agregar productos"""
    return redirect(url_for('agregar_producto'))

@app.route('/listar_productos')
def listar_productos():
    if 'usuario' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM productos ORDER BY id DESC")
        productos = cur.fetchall()
        cur.close()
        return render_template("listar_productos.html", 
                             usuario=session['usuario'], 
                             productos=productos)
    else:
        return redirect(url_for('login'))

@app.route('/editar_producto/<int:id>', methods=['POST'])
def editar_producto(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cur.execute("SELECT * FROM productos WHERE id = %s", (id,))
    producto = cur.fetchone()

    if not producto:
        flash("Producto no encontrado", "warning")
        cur.close()
        return redirect(url_for('listar_productos'))

    accion = request.form.get('accion')
    if accion == 'eliminar':
        cur.execute("DELETE FROM productos WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        flash("Producto eliminado correctamente!", "success")
        return redirect(url_for('listar_productos'))

    nombre = request.form['nombre']
    precio = float(request.form['precio'])
    descripcion = request.form['descripcion']
    fecha = request.form.get('fecha')

    cur.execute("""
        UPDATE productos
        SET nombre=%s, precio=%s, descripcion=%s, fecha=%s
        WHERE id=%s
    """, (nombre, precio, descripcion, fecha, id))
    mysql.connection.commit()
    cur.close()

    flash("Producto actualizado correctamente!", "success")
    return redirect(url_for('listar_productos'))

# ----------------- MIGRACIÓN AUTOMÁTICA -----------------
def migrar_contraseñas_automaticamente():
    """Migra automáticamente las contraseñas que no estén en formato bcrypt"""
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, password FROM usuario WHERE password IS NOT NULL")
        usuarios = cur.fetchall()
        
        migrados = 0
        for usuario in usuarios:
            if usuario['password'] and not is_bcrypt_hash(usuario['password']):
                # La contraseña está en texto plano, migrarla
                hashed_password = hash_password(usuario['password'])
                if hashed_password:
                    cur.execute("UPDATE usuario SET password = %s WHERE id = %s", 
                               (hashed_password, usuario['id']))
                    migrados += 1
                    print(f"Migrado usuario ID: {usuario['id']}")
        
        mysql.connection.commit()
        cur.close()
        print(f"Migración completada. {migrados} usuarios migrados.")
        return migrados
    except Exception as e:
        print(f"Error en migración automática: {e}")
        return 0

@app.route('/acercade')
def acercade():
    return render_template("acercade.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    # Ejecutar migración automática al inicio
    print("Ejecutando migración automática de contraseñas...")
    migrados = migrar_contraseñas_automaticamente()
    if migrados > 0:
        print(f"Se migraron {migrados} contraseñas a formato bcrypt")
    
    app.run(debug=True, port=8000)