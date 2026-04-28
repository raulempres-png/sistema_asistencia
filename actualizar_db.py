import sqlite3

def actualizar():
    conn = sqlite3.connect('asistencia.db')
    cursor = conn.cursor()
    
    try:
        # 1. Agregamos la columna para la huella digital de la foto
        cursor.execute("ALTER TABLE empleados ADD COLUMN hash_foto TEXT")
        print("✅ Columna 'hash_foto' añadida con éxito.")
    except sqlite3.OperationalError:
        print("⚠️ La columna 'hash_foto' ya existía.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    actualizar()