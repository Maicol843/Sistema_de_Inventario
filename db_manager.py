import sqlite3
from sqlite3 import Error

# Nombre del archivo de la base de datos
DB_FILE = 'inventario.db'

class DBManager:
    """Clase para manejar las operaciones de la base de datos SQLite."""

    def __init__(self):
        """Inicializa la conexión y se asegura de que las tablas existan."""
        self.conn = self._create_connection()
        if self.conn:
            self._create_tables()

    def _create_connection(self):
        """Crea una conexión a la base de datos SQLite especificada por DB_FILE."""
        conn = None
        try:
            conn = sqlite3.connect(DB_FILE, check_same_thread=False) 
            conn.execute("PRAGMA foreign_keys = ON;")
            print("Conexión a la base de datos SQLite exitosa.")
            return conn
        except Error as e:
            print(f"Error al conectar a la base de datos: {e}")
            return conn

    def _create_tables(self):
        """Crea las tablas 'categorias', 'productos' y 'movimientos' si aún no existen."""
        create_categorias_table = """
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        );
        """
        create_productos_table = """
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            categoria_id INTEGER,
            laboratorio TEXT,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id)
        );
        """
        create_movimientos_table = """
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('Compra', 'Venta')),
            precio REAL NOT NULL,
            cantidad INTEGER NOT NULL,
            observaciones TEXT,
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        );
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(create_categorias_table)
            cursor.execute(create_productos_table)
            cursor.execute(create_movimientos_table)
            self.conn.commit()
            print("Tablas 'categorias', 'productos' y 'movimientos' verificadas/creadas exitosamente.")
        except Error as e:
            print(f"Error al crear las tablas: {e}")

    # --- Operaciones de Utilidad General ---
    
    def obtener_productos_combo(self):
        """Recupera el ID y el Nombre de todos los productos para usar en ComboBox."""
        sql = "SELECT id, nombre FROM productos ORDER BY nombre ASC"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener productos para combo: {e}")
            return []

    def obtener_id_producto_por_nombre(self, nombre):
        """Busca el ID de un producto a partir de su nombre."""
        sql = "SELECT id FROM productos WHERE nombre = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (nombre,))
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None
        except Error as e:
            print(f"Error al obtener ID de producto: {e}")
            return None

    def obtener_producto_por_id(self, producto_id):
        """Recupera todos los datos de un producto por su ID."""
        sql = """
        SELECT
            p.codigo,
            p.nombre,
            c.nombre as categoria,
            p.laboratorio
        FROM productos p
        INNER JOIN categorias c ON p.categoria_id = c.id
        WHERE p.id = ?
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (producto_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error al obtener producto por ID: {e}")
            return None

    def eliminar_producto_completo(self, producto_id):
        """
        Elimina el producto y todos sus movimientos asociados (CASCADE LIKE).
        Nota: SQLite necesita PRAGMA foreign_keys = ON, que ya está configurado.
        """
        try:
            self.conn.execute("BEGIN TRANSACTION")
            
            # 1. Eliminar movimientos asociados
            self.conn.execute("DELETE FROM movimientos WHERE producto_id = ?", (producto_id,))
            
            # 2. Eliminar el producto
            self.conn.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
            
            self.conn.commit()
            return True
        except Error as e:
            self.conn.rollback()
            print(f"Error al eliminar producto completo: {e}")
            return False
            
    # --- Nueva Operación Central para el Módulo Inventario ---
    
    def obtener_datos_inventario(self):
        """
        Consulta todos los productos y calcula su stock actual 
        basándose en los movimientos (compras suman, ventas restan).
        """
        sql = """
        SELECT
            p.id,
            p.codigo,
            p.nombre,
            c.nombre as categoria,
            p.laboratorio,
            COALESCE(SUM(
                CASE 
                    WHEN m.tipo = 'Compra' THEN m.cantidad 
                    WHEN m.tipo = 'Venta' THEN -m.cantidad
                    ELSE 0 
                END
            ), 0) AS stock_actual
        FROM productos p
        INNER JOIN categorias c ON p.categoria_id = c.id
        LEFT JOIN movimientos m ON p.id = m.producto_id
        GROUP BY p.id, p.codigo, p.nombre, c.nombre, p.laboratorio
        ORDER BY p.nombre ASC;
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            # Retorna una lista de tuplas con (id, codigo, nombre, categoria, laboratorio, stock_actual)
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener datos de inventario: {e}")
            return []

    # --- Operaciones CRUD para Categorías ---
    # ... [Todas las funciones de Categorías se mantienen igual] ...
    def insertar_categoria(self, nombre):
        sql = "INSERT INTO categorias (nombre) VALUES (?)"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (nombre,))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return "DUPLICATE"
        except Error as e:
            return None

    def obtener_categorias(self):
        sql = "SELECT id, nombre FROM categorias ORDER BY id DESC"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            return cursor.fetchall()
        except Error as e:
            return []

    def obtener_todas_categorias_combo(self):
        sql = "SELECT nombre FROM categorias ORDER BY nombre ASC"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            return [row[0] for row in cursor.fetchall()]
        except Error as e:
            return []
            
    def obtener_id_categoria_por_nombre(self, nombre):
        sql = "SELECT id FROM categorias WHERE nombre = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (nombre,))
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None
        except Error as e:
            return None

    def actualizar_categoria(self, categoria_id, nuevo_nombre):
        sql = "UPDATE categorias SET nombre = ? WHERE id = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (nuevo_nombre, categoria_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return "DUPLICATE"
        except Error as e:
            return False

    def eliminar_categoria(self, categoria_id):
        sql = "DELETE FROM categorias WHERE id = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (categoria_id,))
            self.conn.commit()
            return True
        except Error as e:
            return False
            
    # --- Operaciones CRUD para Productos ---
    
    def insertar_producto(self, codigo, nombre, categoria_id, laboratorio):
        """Inserta un nuevo producto en la base de datos."""
        sql = "INSERT INTO productos (codigo, nombre, categoria_id, laboratorio) VALUES (?, ?, ?, ?)"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (codigo, nombre, categoria_id, laboratorio))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return "DUPLICATE_CODE"
        except Error as e:
            return None
            
    # --- Operación para Movimientos ---
    
    def insertar_movimiento(self, producto_id, fecha, tipo, precio, cantidad, observaciones):
        """Inserta un nuevo movimiento (Compra/Venta) en la base de datos."""
        sql = """
        INSERT INTO movimientos (producto_id, fecha, tipo, precio, cantidad, observaciones) 
        VALUES (?, ?, ?, ?, ?, ?)
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (producto_id, fecha, tipo, precio, cantidad, observaciones))
            self.conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Error al insertar movimiento: {e}")
            return None

    def __del__(self):
        """Cierra la conexión cuando el objeto es destruido."""
        if self.conn:
            self.conn.close()

# --- Fin de db_manager.py ---