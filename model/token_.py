from functools import wraps

import jwt
from flask import request, jsonify, current_app

from bd import BaseDeDatos


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        print(request.headers)
        # Obtener el token del encabezado de la solicitud
        if 'Authorization' in request.headers:
            try:
                # Obtener el token después de 'Bearer'
                token = request.headers['Authorization'].split()[1]
            except IndexError:
                return jsonify({"error": "Token es requerido2"}), 401

        if not token:
            return jsonify({"error": "Token es requerido1"}), 401

        try:
            # Decodificar el token JWT
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            # Obtener el usuario actual usando el ID en el token
            print(data['user_id'])
            current_user = BaseDeDatos().obtener_usuario_por_id(data['user_id'])
            if not current_user:
                return jsonify({"error": "Usuario no encontrado"}), 404

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token ha expirado, por favor inicie sesión de nuevo"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido, por favor inicie sesión de nuevo"}), 401

        # Si
        return f(current_user, *args, **kwargs)

    return decorated
