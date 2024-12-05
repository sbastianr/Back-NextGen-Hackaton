import os
from datetime import datetime

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

    def guardar_usuario(self, nombre, telefono, email, password, public_key):
        """Guarda un usuario en la tabla 'usuario' con su nombre y public key."""
        try:
            conn = self.obtener_conexion()
            cursor = conn.cursor()

            # Inserta el usuario en la tabla 'usuario'
            sql = "INSERT INTO Usuario (Name, PublicKey, Telefono, Email, Password) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (nombre, public_key, telefono, email, password))

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

            sql = "SELECT * FROM Usuario WHERE Email = %s"
            cursor.execute(sql, (email,))
            user = cursor.fetchone()

            cursor.close()
            return user

        except mysql.connector.Error as e:
            print(f"Error al obtener el usuario: {e}")
            return None

    def obtener_lista_empleados(self):
        """Obtiene la lista de correos electrónicos de los empleados de la base de datos."""
        try:
            conn = self.obtener_conexion()
            cursor = conn.cursor(dictionary=True)

            sql = "SELECT email FROM Usuario"
            cursor.execute(sql)
            correos = cursor.fetchall()

            cursor.close()
            return correos

        except mysql.connector.Error as e:
            print(f"Error al obtener la lista de correos electrónicos: {e}")
            return []

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

    def guardar_archivo(self, filename, file_data, user_id, hash_sha256, correos_usuario):
        try:
            conn = self.obtener_conexion()
            cursor = conn.cursor(dictionary=True)

            sql = "INSERT INTO File (nombre_archivo, contenido_archivo, usuario_id, hash) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (filename, file_data, user_id, hash_sha256))
            archivo_id = cursor.lastrowid

            for correo_user in correos_usuario:
                sql_usuario = "SELECT id FROM Usuario WHERE email = %s"
                cursor.execute(sql_usuario, (correo_user,))
                result = cursor.fetchone()  # Obtiene el primer resultado

                if result:
                    usuario_id = result['id']  # Asume que 'usuario_id' es la primera columna en el resultado

                    # 2. Realizar la inserción en la tabla Firma
                    sql_firma = "INSERT INTO Firma (archivo_id, usuario_id, estado_firma) VALUES (%s, %s, %s)"
                    cursor.execute(sql_firma, (archivo_id, usuario_id, 0))

            conn.commit()
            cursor.close()

        except mysql.connector.Error as e:
            print(f"Error al obtener el usuario: {e}")
            return None

    def obtener_archivo_por_id(self, archivo_id):
        # Conectar a la base de datos y ejecutar la consulta
        conn = self.obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        # Consultar el archivo por su ID
        sql = "SELECT nombre_archivo, contenido_archivo FROM File WHERE id = %s"
        cursor.execute(sql, (archivo_id,))

        # Obtener el resultado
        resultado = cursor.fetchone()
        print(type(resultado))
        cursor.close()
        conn.close()

        if resultado:
            return {
                "nombre_archivo": resultado["nombre_archivo"],
                "contenido_archivo": resultado["contenido_archivo"]
            }
        else:
            return None


    def obtener_archivos_por_usuario_y_estado(self, usuario_id):
        # Conectar a la base de datos y ejecutar la consulta
        conn = self.obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        # Consulta para obtener los archivos según el usuario_id y estado_firma = 0
        sql = """
            SELECT fi.nombre_archivo, fi.hash, fi.id
            FROM Firma f
            JOIN File fi ON f.archivo_id = fi.id
            WHERE f.usuario_id = %s
            AND f.estado_firma = 0
        """
        cursor.execute(sql, (usuario_id,))

        # Obtener todos los resultados
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()

        if resultados:
            return resultados  # Devuelve una lista de archivos
        else:
            return None

    def obtener_llave_publica(self, usuario_id):
        conn = self.obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        # Consulta para obtener los archivos según el usuario_id y estado_firma = 0
        sql = """
                    SELECT PublicKey
                    FROM Usuario
                    WHERE id = %s
                """
        cursor.execute(sql, (usuario_id,))

        # Obtener todos los resultados
        resultados = cursor.fetchone()
        cursor.close()
        conn.close()

        if resultados:
            return resultados  # Devuelve una lista de archivos
        else:
            return None

    def actualizar_firma(self, usuario_id, hash_file, firma):
        print("Iniciando actualización de firma")

        # Obtener conexión
        conn = self.obtener_conexion()
        if conn is None:
            print("No se pudo establecer conexión con la base de datos")
            return

        print("Conexión establecida con éxito")
        # Verificar si la conexión sigue activa
        if not conn.is_connected():
            print("La conexión a MySQL se ha perdido")
            return
        try:
            cursor = conn.cursor(dictionary=True)
            print("Cursor creado correctamente")

            # Consulta SQL para actualizar la firma
            sql = """
            UPDATE Firma f
            JOIN File fi ON f.archivo_id = fi.id
            SET f.firma = %s, 
                f.fecha_firma = NOW(),
                f.estado_firma = 1
            WHERE fi.hash = %s
            AND f.usuario_id = %s;
            """

            # Ejecutar la consulta con los valores proporcionados
            cursor.execute(sql, (firma, hash_file, usuario_id))
            print("Consulta ejecutada correctamente")

            # Confirmar la transacción
            conn.commit()
            print("Transacción confirmada. Firma actualizada.")

        except mysql.connector.Error as e:
            print(f"Error al actualizar la firma: {e}")

        finally:
            # Cerrar el cursor y la conexión si están abiertos
            if conn.is_connected():
                cursor.close()
                conn.close()
                print("Conexión cerrada correctamente")

    def usuarios_firmaron_by_id(self, usuario_id):
        # Conectar a la base de datos y ejecutar la consulta
        conn = self.obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        # Consulta para obtener los archivos según el usuario_id y estado_firma = 0
        sql = """
                    SELECT u.Email
                    FROM Firma f
                    JOIN Usuario u ON f.usuario_id = u.id
                    WHERE f.archivo_id = %s AND f.estado_firma = %s;

                """
        cursor.execute(sql, (usuario_id, 1))

        # Obtener todos los resultados
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()

        if resultados:
            return resultados  # Devuelve una lista de archivos
        else:
            return None