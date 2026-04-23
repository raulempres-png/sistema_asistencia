from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'trexcel_secreto_2026'

def get_db_connection():
    conn = sqlite3.connect('asistencia.db')
    conn.row_factory = sqlite3.Row
    return conn

# Sincronización directa con el reloj de tu Windows
def get_peru_time():
    return datetime.now()

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
            # Lógica de tardanza: 8:00 AM
            if tipo.upper() == "INGRESO" and ahora.hour >= 8: 
                estado = "OBSERVADO - TARDE"
            
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