import sqlite3

def actualizar():
    conn = sqlite3.connect('asistencia.db')
    cursor = conn.cursor()
    
    # 1. Agregamos la columna de categoría (Empleado/Teletram)
    try:
        cursor.execute("ALTER TABLE empleados ADD COLUMN categoria TEXT DEFAULT 'EMPLEADO'")
        print("✅ Columna 'categoria' añadida con éxito.")
    except sqlite3.OperationalError:
        print("⚠️ La columna 'categoria' ya existía.")

    # 2. Agregamos la columna para la huella digital de la foto
    try:
        cursor.execute("ALTER TABLE empleados ADD COLUMN hash_foto TEXT")
        print("✅ Columna 'hash_foto' añadida con éxito.")
    except sqlite3.OperationalError:
        print("⚠️ La columna 'hash_foto' ya existía.")

    conn.commit()
    conn.close()
    print("🎉 Actualización de base de datos finalizada.")

if __name__ == "__main__":
    actualizar()