import base64

import bcrypt

# Almacenar el hash con salt
def generar_password_hash(password):
    # Generar la salt y crear el hash
    hash_con_salt = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hash_con_salt


# Verificar la contraseña
def verificar_password_hash(password, hash_almacenado):
    # Verificar si la contraseña coincide con el hash almacenado
    return bcrypt.checkpw(password.encode('utf-8'), hash_almacenado)


def validar_todos_los_campos(data):
    """Valida que todos los campos del diccionario tengan valores no vacíos.

    Args:
        data (dict): Los datos del request JSON.

    Returns:
        tuple: (bool, mensaje de error o None).
    """
    for campo, valor in data.items():
        if not valor:  # Revisa si está vacío o es None
            return False, f"El campo '{campo}' es obligatorio."
    return True, None

