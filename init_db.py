import sqlite3

def crear_tablas():
    conexion = sqlite3.connect('asistencia.db')
    cursor = conexion.cursor()

    # Tabla de Supervisores (Para el Login)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS supervisores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL
        )
    ''')

    # Tabla de Empleados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empleados (
            dni TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            contrata TEXT NOT NULL,
            supervisor_id INTEGER,
            FOREIGN KEY(supervisor_id) REFERENCES supervisores(id)
        )
    ''')

    # Tabla de Asistencia
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dni_empleado TEXT NOT NULL,
            tipo_movimiento TEXT NOT NULL, -- 'INGRESO' o 'SALIDA'
            fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
            estado TEXT, -- 'OK' o 'OBSERVADO'
            FOREIGN KEY(dni_empleado) REFERENCES empleados(dni)
        )
    ''')

    # Crear un usuario administrador por defecto
    cursor.execute("INSERT OR IGNORE INTO supervisores (usuario, password, rol) VALUES ('admin', 'admin123', 'maestro')")
    cursor.execute("INSERT OR IGNORE INTO supervisores (usuario, password, rol) VALUES ('supervisor1', '1234', 'supervisor')")

    conexion.commit()
    conexion.close()
    print("Base de datos creada exitosamente.")

if __name__ == '__main__':
    crear_tablas()