import os
import sqlite3
import hashlib # Para el "ojo digital"
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'trexcel_secreto_2026'

UPLOAD_FOLDER = 'static/fotos_empleados'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect('asistencia.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_peru_time():
    return datetime.utcnow() - timedelta(hours=5)

@app.route('/')
def index():
    if 'usuario' in session: return redirect(url_for('panel'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    u = request.form['usuario']; p = request.form['password']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM supervisores WHERE usuario = ? AND password = ?', (u, p)).fetchone()
    conn.close()
    if user:
        session['usuario'] = user['usuario']; session['rol'] = user['rol']; session['user_id'] = user['id']
        return redirect(url_for('panel'))
    flash('Credenciales incorrectas', 'danger')
    return redirect(url_for('index'))

@app.route('/panel')
def panel():
    if 'usuario' not in session: return redirect(url_for('index'))
    return render_template('panel.html', rol=session['rol'], usuario=session['usuario'])

# --- REGISTRO CON OJO DIGITAL (DETECCIÓN DE DUPLICADOS) ---
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if 'usuario' not in session or session['rol'] not in ['supervisor', 'maestro']: return redirect(url_for('panel'))
    if request.method == 'POST':
        dni = request.form['dni']; nombre = request.form['nombre']
        apellido = request.form['apellido']; contrata = request.form['contrata']
        categoria = request.form.get('categoria', 'EMPLEADO')
        
        filename_db = 'default_user.png'
        hash_actual = None

        if 'foto' in request.files:
            file = request.files['foto']
            if file and allowed_file(file.filename):
                # OJO DIGITAL: Generamos la huella única de la imagen
                contenido = file.read()
                hash_actual = hashlib.md5(contenido).hexdigest()
                file.seek(0) 

                conn = get_db_connection()
                duplicado = conn.execute('SELECT nombre, apellido FROM empleados WHERE hash_foto = ?', (hash_actual,)).fetchone()
                conn.close()

                if duplicado:
                    flash(f'⚠️ ERROR: Esta foto ya fue usada para {duplicado["nombre"]} {duplicado["apellido"]}. Use una foto real del nuevo empleado.', 'danger')
                    return redirect(url_for('registro'))

                extension = file.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"{dni}.{extension}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                filename_db = filename

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO empleados (dni, nombre, apellido, contrata, supervisor_id, foto, categoria, hash_foto) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                         (dni, nombre, apellido, contrata, session['user_id'], filename_db, categoria, hash_actual))
            conn.commit()
            flash('Empleado registrado exitosamente', 'success')
        except: flash('Error: El DNI ya existe', 'danger')
        finally: conn.close()
        return redirect(url_for('registro'))
    return render_template('registro.html', usuario=session['usuario'])

# --- NUEVA RUTA: CAMBIO DE CONTRASEÑA POR MAESTRO ---
@app.route('/cambiar_password/<int:id>', methods=['POST'])
def cambiar_password(id):
    if session.get('rol') != 'maestro': return redirect(url_for('panel'))
    nueva_p = request.form['nueva_p']
    conn = get_db_connection()
    conn.execute('UPDATE supervisores SET password = ? WHERE id = ?', (nueva_p, id))
    conn.commit()
    conn.close()
    flash('Contraseña actualizada correctamente', 'success')
    return redirect(url_for('gestion_usuarios'))

# (Aquí van el resto de tus rutas: escaneo, lista_empleados, etc...)

@app.route('/gestion_usuarios', methods=['GET', 'POST'])
def gestion_usuarios():
    if session.get('rol') != 'maestro': return redirect(url_for('panel'))
    conn = get_db_connection()
    if request.method == 'POST':
        u = request.form['u']; p = request.form['p']; r = request.form['r']
        try:
            conn.execute('INSERT INTO supervisores (usuario, password, rol) VALUES (?, ?, ?)', (u, p, r))
            conn.commit()
            flash('Usuario creado', 'success')
        except: flash('El usuario ya existe', 'danger')
    users = conn.execute('SELECT * FROM supervisores').fetchall()
    conn.close()
    return render_template('gestion_usuarios.html', users=users)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)