import datetime

import jwt
from authlib.integrations.flask_client import OAuth
from flask import Flask
from flask import request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

from bd import BaseDeDatos
from model import utils
from model.token_ import token_required

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SECRET_KEY'] = 'test'
oauth = OAuth(app)


@app.route('/register', methods=['GET', 'POST'])
def register():
    data = request.get_json()
    bd = BaseDeDatos()

    # Validar todos los campos
    es_valido, mensaje_error = utils.validar_todos_los_campos(data)
    if not es_valido:
        return jsonify({"error": mensaje_error}), 400

    respuesta = bd.guardar_usuario(first_name=data['first_name'], last_name=data['last_name'],
                                   email=data.get('email'), mobile=data['mobile'],
                                   city=data['city'], address=data['address'],
                                   birth_date=data['birth_date'],
                                   registration_date=datetime.now(),
                                   password=utils.generar_password_hash(data.get('password')))

    return jsonify(respuesta), 201


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
    if not utils.verificar_password_hash(password, user['password'].encode('utf-8')):
        return jsonify({"error": "Correo o contraseña incorrectos 2"}), 401

    token = jwt.encode({
        'user_id': user['id_user'],
        'exp': datetime.now() + timedelta(minutes=500)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token, 'message': 'Inicio de sesión exitoso'}), 200


@app.route('/products', methods=['GET'])
@token_required
def obetenr_todos_productos():
    bd = BaseDeDatos()
    productos = bd.obtener_todos_productos()


    return jsonify(productos), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
