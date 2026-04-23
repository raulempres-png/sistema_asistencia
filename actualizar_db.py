import sqlite3

try:
    conn = sqlite3.connect('asistencia.db')
    # Usamos comillas dobles afuera y simples adentro para no fallar
    conn.execute("ALTER TABLE empleados ADD COLUMN foto TEXT DEFAULT 'default_user.png'")
    conn.commit()
    conn.close()
    print("✅ ¡Éxito! Columna 'foto' añadida correctamente.")
except Exception as e:
    print(f"❌ Error: {e}")