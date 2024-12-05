import datetime
import hashlib
import io

import jwt
from authlib.integrations.flask_client import OAuth
from flask import Flask
from flask import request, jsonify
from flask import send_file
from flask_cors import CORS

import Utils
from bd import BaseDeDatos
from RSAKeyGenerator import RSAKeyGenerator
from token_ import token_required

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SECRET_KEY'] = 'test'
oauth = OAuth(app)

@app.route('/register', methods=['GET', 'POST'])
def register():
    data = request.get_json()
    bd = BaseDeDatos()

    rsa_generator = RSAKeyGenerator()
    rsa_generator.generate_keys()
    private_key_pem = rsa_generator.get_private_key_pem()
    public_key_pem = rsa_generator.get_public_key_pem()

    name = data['nombre']
    telefono = data['telefono']
    email = data.get('email')
    password = data.get('password')
    password = Utils.generar_password_hash(password)

    if not (name and telefono and password and email):
        return jsonify({"error": "Llene todos los campos"}), 400

    if not bd.verificar_correo_existente(email):
        return jsonify({"error": "El correo ya esta en uso"}), 400

    respuesta = bd.guardar_usuario(nombre=name, telefono=telefono,
                                   email=email, password=password, public_key=public_key_pem)

    response = {
        "message": "Usuario guardado exitosamente",
        "name": name,
        "privateKey": private_key_pem,
        "respuesta": respuesta
    }

    return jsonify(response), 201


@app.route('/inicio_sesion', methods=['POST'])
def login():

    data = request.get_json()
    bd = BaseDeDatos()

    email = data['email']
    password = data['password']

    if not email or not password:
        return jsonify({"error": "Llene todos los campos"}), 400

    # Verificar si el usuario existe en la base de datos
    user = bd.obtener_usuario_por_email(email)
    if not user:
        return jsonify({"error": "Correo o contraseña incorrectos 1"}), 401

    # Verificar la contraseña
    if not Utils.verificar_password_hash(password, user['Password'].encode('utf-8')):
        return jsonify({"error": "Correo o contraseña incorrectos 2"}), 401

    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.datetime.now() + datetime.timedelta(minutes=500)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token, 'message': 'Inicio de sesión exitoso'}), 200


@app.route('/lista_usuarios', methods=['GET'])
@token_required
def lista_usuarios(current_user):
    bd = BaseDeDatos()
    usuarios = bd.obtener_lista_empleados()

    emails_str = ','.join([email['email'] for email in usuarios])
    result = {'email': emails_str}

    return jsonify(result), 200


@app.route('/lista_archivos_firmar', methods=['GET'])
@token_required
def lista_archivos_firmar(current_user):
    bd = BaseDeDatos()
    files = bd.obtener_archivos_por_usuario_y_estado(current_user['id'])
    print(files)
    lista_nueva = []
    for file in files:
        file_nuevo = file
        bd = BaseDeDatos()

        usuarios_firmaron = bd.usuarios_firmaron_by_id(file["id"])
        firmaron = ""
        if usuarios_firmaron:
            firmaron = ','.join([correo['Email'] for correo in usuarios_firmaron])
        file_nuevo['firmaron'] = firmaron

        lista_nueva.append(file_nuevo)

    return jsonify(lista_nueva), 200


@app.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    bd = BaseDeDatos()

    if 'file' not in request.files:
        return jsonify({"error": "No se ha enviado ningún archivo"}), 400

    codigos_usuario_str = request.args.get('codigos_usuario')
    if not codigos_usuario_str:
        return jsonify({"error": "No se ha enviado ningún código de usuario"}), 400
    correos_usuario = codigos_usuario_str.split(',')
    correos_usuario = [codigo.strip() for codigo in correos_usuario]  # Limpiar espacios

    file = request.files['file']

    # Verificar que el archivo no esté vacío
    if file.filename == '':
        return jsonify({"error": "El archivo está vacío"}), 400

    # Procesar el archivo (por ejemplo, guardarlo o almacenarlo en base de datos)
    file_data = file.read()
    hash_sha256 = hashlib.sha256(file_data).hexdigest()

    bd.guardar_archivo(file.filename, file_data, current_user['id'], hash_sha256, correos_usuario)

    return jsonify({"message": "Archivo recibido exitosamente", "filename": file.filename}), 200


@app.route('/download', methods=['GET'])
@token_required
def descargar_archivo(current_user):
    bd = BaseDeDatos()
    data = request.get_json()

    archivo_id = data['archivo_id']

    # Obtener el archivo desde la base de datos usando el ID
    archivo = bd.obtener_archivo_por_id(archivo_id)

    if archivo is None:
        return jsonify({"error": "Archivo no encontrado"}), 404

    # Crear un archivo en memoria (usando io.BytesIO)
    file_data = io.BytesIO(archivo['contenido_archivo'])
    file_data.seek(0)

    # Enviar el archivo usando send_file de Flask
    return send_file(
        file_data,
        as_attachment=True,
        download_name=archivo['nombre_archivo']  # Nombre del archivo a descargar
    )


@app.route('/firmar_archivo', methods=['POST'])
@token_required
def firmar_archivo(current_user):
    bd = BaseDeDatos()
    hash_file = request.args.get('hash_file')

    if 'privateKey' not in request.files:
        return jsonify({'message': 'Se requiere el archivo .pem con la llave privada y el ID de usuario'}), 400

        # Obtener la llave privada del archivo .pem y el usuario_id del formulario
    private_key_pem = request.files['privateKey'].read().decode("utf-8")
    private_key_pem = Utils.formatear_llave_privada(private_key_pem)
    usuario_id = current_user['id']

    # Obtener la llave pública desde la base de datos
    result = bd.obtener_llave_publica(usuario_id)

    if not result:
        return jsonify({'message': 'No se encontró la llave pública para el usuario proporcionado'}), 404

    try:
        # Cargar las llaves
        private_key = Utils.cargar_llave_privada(private_key_pem.encode('utf-8'))
        public_key = Utils.cargar_llave_publica(result["PublicKey"])

        firma = Utils.firmar_mensaje(private_key, hash_file.encode('utf-8'))
        # Verificar la firma con la llave pública
        if Utils.verificar_firma(public_key, hash_file.encode("utf-8"), firma):
            print("ish")
            bd = BaseDeDatos()
            bd.actualizar_firma(usuario_id, hash_file, Utils.firma_a_base64(firma))
            return jsonify({'message': 'Las llaves corresponden. La firma es válida.'})
        else:
            return jsonify({'message': 'Las llaves NO corresponden.'}), 400

    except Exception as e:
        return jsonify({'message': 'Error al procesar las llaves.', 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
