import jwt
from config import algorithm, private_key_path, public_key_path


def encode_jwt(payload: dict, private_key: str = private_key_path.read_text(), algorithm: str = algorithm):
    encoded = jwt.encode(payload, private_key, algorithm=algorithm)
    return encoded


def decode_jwt(token: str | bytes, public_key: str = public_key_path.read_text(), algorithm: str = algorithm):
    decoded = jwt.decode(token, public_key, algorithms=[algorithm])
    return decoded
