import sqlite3

def inicializar_tabla_usuarios():
    conexion = sqlite3.connect('expedientes.db')
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT UNIQUE,
            password TEXT
        )
    ''')
    # Insertar un par de empresas de prueba iniciales
    cursor.execute("INSERT OR IGNORE INTO usuarios (empresa, password) VALUES ('Despacho Juridico Garcia', 'garcia2026')")
    cursor.execute("INSERT OR IGNORE INTO usuarios (empresa, password) VALUES ('Financiera del Norte', 'norte2026')")
    conexion.commit()
    conexion.close()

def verificar_credenciales(empresa, password):
    inicializar_tabla_usuarios()
    conexion = sqlite3.connect('expedientes.db')
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE empresa = ? AND password = ?", (empresa, password))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado is not None