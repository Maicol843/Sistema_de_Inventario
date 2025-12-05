import sqlite3
from sqlite3 import Error

# Nombre del archivo de la base de datos
DB_FILE = 'inventario.db'

class DBManager:
    """Clase para manejar las operaciones de la base de datos SQLite."""

    def __init__(self):
        """Inicializa la conexión y se asegura de que la tabla 'categorias' exista."""
        self.conn = self._create_connection()
        if self.conn:
            self._create_tables()

    def _create_connection(self):
        """Crea una conexión a la base de datos SQLite especificada por DB_FILE."""
        conn = None
        try:
            conn = sqlite3.connect(DB_FILE)
            print("Conexión a la base de datos SQLite exitosa.")
            return conn
        except Error as e:
            print(f"Error al conectar a la base de datos: {e}")
            return conn

    def _create_tables(self):
        """Crea la tabla 'categorias' si aún no existe."""
        create_categorias_table = """
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        );
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(create_categorias_table)
            self.conn.commit()
            print("Tabla 'categorias' verificada/creada exitosamente.")
        except Error as e:
            print(f"Error al crear las tablas: {e}")

    # --- Operaciones CRUD para Categorías ---

    def insertar_categoria(self, nombre):
        """Inserta una nueva categoría en la base de datos."""
        sql = "INSERT INTO categorias (nombre) VALUES (?)"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (nombre,))
            self.conn.commit()
            return cursor.lastrowid # Retorna el ID de la fila insertada
        except sqlite3.IntegrityError:
            # Error si el nombre ya existe (UNIQUE constraint)
            return "DUPLICATE"
        except Error as e:
            print(f"Error al insertar categoría: {e}")
            return None

    def obtener_categorias(self):
        """Recupera todas las categorías."""
        sql = "SELECT id, nombre FROM categorias ORDER BY id DESC"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            filas = cursor.fetchall()
            return filas
        except Error as e:
            print(f"Error al obtener categorías: {e}")
            return []

    def actualizar_categoria(self, categoria_id, nuevo_nombre):
        """Actualiza el nombre de una categoría."""
        sql = "UPDATE categorias SET nombre = ? WHERE id = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (nuevo_nombre, categoria_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return "DUPLICATE"
        except Error as e:
            print(f"Error al actualizar categoría: {e}")
            return False

    def eliminar_categoria(self, categoria_id):
        """Elimina una categoría por su ID."""
        sql = "DELETE FROM categorias WHERE id = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (categoria_id,))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Error al eliminar categoría: {e}")
            return False

    def __del__(self):
        """Cierra la conexión cuando el objeto es destruido."""
        if self.conn:
            self.conn.close()