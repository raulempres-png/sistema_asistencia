from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'trexcel_secreto_2026'

def get_db_connection():
    conn = sqlite3.connect('asistencia.db')
    conn.row_factory = sqlite3.Row
    return conn

# Función para la nube: PythonAnywhere usa UTC, por lo que restamos 5 horas para Perú
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

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if 'usuario' not in session: return redirect(url_for('index'))
    if request.method == 'POST':
        dni = request.form['dni']; nombre = request.form['nombre']
        apellido = request.form['apellido']; contrata = request.form['contrata']
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO empleados (dni, nombre, apellido, contrata, supervisor_id) VALUES (?, ?, ?, ?, ?)',
                         (dni, nombre, apellido, contrata, session['user_id']))
            conn.commit()
            flash('Empleado registrado exitosamente', 'success')
        except: flash('Error: El DNI ya existe', 'danger')
        finally: conn.close()
        return redirect(url_for('registro'))
    return render_template('registro.html', usuario=session['usuario'])

@app.route('/lista_empleados')
def lista_empleados():
    if 'usuario' not in session: return redirect(url_for('index'))
    conn = get_db_connection()
    empleados = conn.execute('''
        SELECT e.*, s.usuario as supervisor 
        FROM empleados e 
        JOIN supervisores s ON e.supervisor_id = s.id 
        ORDER BY e.apellido ASC
    ''').fetchall()
    conn.close()
    return render_template('lista_empleados.html', empleados=empleados, rol=session['rol'])

@app.route('/asistencia_log')
def asistencia_log():
    if 'usuario' not in session or session['rol'] != 'maestro': return redirect(url_for('panel'))
    fecha_filtro = request.args.get('fecha', get_peru_time().strftime('%Y-%m-%d'))
    conn = get_db_connection()
    registros = conn.execute('''
        SELECT r.fecha_hora, e.nombre, e.apellido, e.dni, e.contrata, r.tipo_movimiento, r.estado
        FROM registros r
        JOIN empleados e ON r.dni_empleado = e.dni
        WHERE date(r.fecha_hora) = ?
        ORDER BY r.fecha_hora DESC
    ''', (fecha_filtro,)).fetchall()
    conn.close()
    return render_template('asistencia_log.html', registros=registros, fecha_sel=fecha_filtro)

@app.route('/reportes')
def reportes():
    if session.get('rol') != 'maestro': return redirect(url_for('panel'))
    conn = get_db_connection()
    stats = conn.execute("SELECT COUNT(*) as total, SUM(CASE WHEN estado='OK' THEN 1 ELSE 0 END) as ok, SUM(CASE WHEN estado LIKE 'OBS%' THEN 1 ELSE 0 END) as obs FROM registros").fetchone()
    obs_contrata = conn.execute("SELECT e.contrata, COUNT(*) as total FROM registros r JOIN empleados e ON r.dni_empleado=e.dni WHERE r.estado LIKE 'OBS%' GROUP BY 1 ORDER BY total DESC").fetchall()
    obs_sup = conn.execute("SELECT s.usuario, COUNT(*) as total FROM registros r JOIN empleados e ON r.dni_empleado=e.dni JOIN supervisores s ON e.supervisor_id=s.id WHERE r.estado LIKE 'OBS%' GROUP BY 1 ORDER BY total DESC").fetchall()
    top = conn.execute("SELECT e.nombre || ' ' || e.apellido as n, COUNT(*) as t FROM registros r JOIN empleados e ON r.dni_empleado=e.dni WHERE r.estado LIKE 'OBS%' GROUP BY 1 ORDER BY t DESC LIMIT 5").fetchall()
    conn.close()
    return render_template('reportes.html', stats=stats, obs_contrata=obs_contrata, obs_supervisor=obs_sup, top_empleados=top)

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

@app.route('/escaneo/<tipo>', methods=['GET', 'POST'])
def escaneo(tipo):
    if 'usuario' not in session: return redirect(url_for('index'))
    mensaje = None; estado_alerta = None
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
            mensaje = f"{emp['nombre']} - {estado}"; estado_alerta = 'success' if estado == "OK" else 'warning'
        else: mensaje = "DNI no registrado"; estado_alerta = 'danger'
        conn.close()
    return render_template('escaneo.html', tipo=tipo.upper(), mensaje=mensaje, estado_alerta=estado_alerta)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)