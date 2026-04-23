import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename # Para manejar nombres de archivos seguros

app = Flask(__name__)
app.secret_key = 'trexcel_secreto_2026'

# CONFIGURACIÓN DE SUBIDA DE FOTOS
UPLOAD_FOLDER = 'static/fotos_empleados'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Asegurar que la carpeta exista
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

# --- RUTA DE REGISTRO ACTUALIZADA CON FOTO ---
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if 'usuario' not in session or session['rol'] not in ['supervisor', 'maestro']: return redirect(url_for('panel'))
    
    if request.method == 'POST':
        dni = request.form['dni']; nombre = request.form['nombre']
        apellido = request.form['apellido']; contrata = request.form['contrata']
        
        # Procesamiento de la Foto
        filename_db = 'default_user.png' # Imagen por defecto si no suben nada
        if 'foto' in request.files:
            file = request.files['foto']
            if file and allowed_file(file.filename):
                # Guardamos la foto con el nombre del DNI para que sea único
                extension = file.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"{dni}.{extension}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                filename_db = filename # Este nombre se guarda en la BD

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO empleados (dni, nombre, apellido, contrata, supervisor_id, foto) VALUES (?, ?, ?, ?, ?, ?)',
                         (dni, nombre, apellido, contrata, session['user_id'], filename_db))
            conn.commit()
            flash('Empleado registrado exitosamente', 'success')
        except: flash('Error: El DNI ya existe', 'danger')
        finally: conn.close()
        return redirect(url_for('registro'))
    return render_template('registro.html', usuario=session['usuario'])

# --- RUTA DE ESCANEO ACTUALIZADA PARA ENVIAR DATOS DE FOTO ---
@app.route('/escaneo/<tipo>', methods=['GET', 'POST'])
def escaneo(tipo):
    if 'usuario' not in session or session['rol'] not in ['guardian', 'maestro']: return redirect(url_for('panel'))
    
    mensaje = None; estado_alerta = None; empleado_datos = None # Nueva variable
    
    if request.method == 'POST':
        dni = request.form['dni']
        conn = get_db_connection()
        emp = conn.execute('SELECT * FROM empleados WHERE dni = ?', (dni,)).fetchone()
        
        if emp:
            ahora = get_peru_time()
            estado = "OK"
            if tipo.upper() == "INGRESO" and ahora.hour >= 8: estado = "OBSERVADO - TARDE"
            
            conn.execute('INSERT INTO registros (dni_empleado, tipo_movimiento, estado, fecha_hora) VALUES (?, ?, ?, ?)', 
                         (dni, tipo.upper(), estado, ahora.strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            
            mensaje = f"{estado}"; estado_alerta = 'success' if estado == "OK" else 'warning'
            # Enviamos los datos completos del empleado a la plantilla
            empleado_datos = emp 
        else: 
            mensaje = "DNI no registrado"; estado_alerta = 'danger'
        conn.close()
    
    return render_template('escaneo.html', tipo=tipo.upper(), mensaje=mensaje, estado_alerta=estado_alerta, empleado=empleado_datos)

# (Rutas de reportes, usuarios, etc. permanecen igual...)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)