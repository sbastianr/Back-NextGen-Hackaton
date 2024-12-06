import os
import mysql.connector
from dotenv import load_dotenv


class BaseDeDatos:
    def __init__(self):
        # Cargar variables de entorno desde el archivo .env
        load_dotenv()

        # Leer variables de entorno
        self.host = os.getenv("DB_HOST")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.database = os.getenv("DB_NAME")

        self.conn = None

    def conectar(self):
        """Establece la conexión a la base de datos."""
        if self.conn is None:
            try:
                self.conn = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    port=3306,
                    charset='utf8mb4',
                    collation='utf8mb4_general_ci'
                )
                print("Conexión a la base de datos establecida exitosamente.")
            except mysql.connector.Error as e:
                print(f"Error conectando a la base de datos: {e}")
                raise

    def obtener_conexion(self):
        """Devuelve la conexión a la base de datos."""
        if self.conn is None:
            self.conectar()
        return self.conn

    def cerrar_conexion(self):
        """Cierra la conexión a la base de datos."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            print("Conexión a la base de datos cerrada.")

    def guardar_usuario(self, first_name, last_name, email, mobile,
                        city, address, birth_date, registration_date, password):
        """Guarda un usuario en la tabla 'usuario' con su nombre y public key."""
        try:
            conn = self.obtener_conexion()
            cursor = conn.cursor()

            # Inserta el usuario en la tabla 'usuario'
            sql = "INSERT INTO users (first_name, last_name, email, mobile, city, address, birth_date, registration_date, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (first_name, last_name, email, mobile, city, address, birth_date, registration_date, password))

            # Confirma la transacción
            conn.commit()
            cursor.close()
            return "Usuario guardado exitosamente."

        except mysql.connector.Error as e:
            return f"Error guardando el usuario: {e}"

    def verificar_correo_existente(self, email):
        """Verifica si un correo electrónico ya existe en la tabla 'Usuarios'."""
        try:
            conn = self.obtener_conexion()
            cursor = conn.cursor()

            # Verificar si el correo ya existe
            sql = "SELECT COUNT(*) FROM Usuario WHERE Email = %s"
            cursor.execute(sql, (email,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] == 0

        except mysql.connector.Error as e:
            print(f"Error verificando el correo: {e}")
            return False

    def obtener_usuario_por_email(self, email):
        """Obtiene un usuario de la base de datos por su email."""
        try:
            conn = self.obtener_conexion()
            cursor = conn.cursor(dictionary=True)

            sql = "SELECT * FROM users WHERE Email = %s"
            cursor.execute(sql, (email,))
            user = cursor.fetchone()

            cursor.close()
            return user

        except mysql.connector.Error as e:
            print(f"Error al obtener el usuario: {e}")
            return None


    def obtener_usuario_por_id(self, id):
        try:
            conn = self.obtener_conexion()
            cursor = conn.cursor(dictionary=True)

            sql = "SELECT * FROM Usuario WHERE id = %s"
            cursor.execute(sql, (id,))
            usuario = cursor.fetchone()

            cursor.close()
        except mysql.connector.Error as e:
            print(f"Error al obtener el usuario: {e}")
            return None
        return usuario

    def obtener_todos_productos(self):
        """Obtiene la lista de correos electrónicos de los empleados de la base de datos."""
        try:
            conn = self.obtener_conexion()
            cursor = conn.cursor(dictionary=True)

            sql = "SELECT * FROM products"
            cursor.execute(sql)
            productos = cursor.fetchall()

            cursor.close()
            return productos

        except mysql.connector.Error as e:
            print(f"Error al obtener los productos: {e}")
            return []
