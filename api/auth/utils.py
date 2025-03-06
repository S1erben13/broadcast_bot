from datetime import timedelta, datetime
import jwt
import bcrypt

from config import algorithm, private_key_path, public_key_path, access_token_expire_minutes


def encode_jwt(payload: dict,
               private_key: str = private_key_path.read_text(),
               algorithm: str = algorithm,
               expire_timedelta: timedelta | None = None,
               expire_minutes: int = access_token_expire_minutes
):
    to_encode = payload.copy()
    now = datetime.utcnow()
    if expire_timedelta:
        expire = now + expire_timedelta
    else:
        expire = now + timedelta(minutes=expire_minutes)
    to_encode.update(exp=expire, iat=now)
    encoded = jwt.encode(to_encode, payload, private_key, algorithm=algorithm)
    return encoded


def decode_jwt(token: str | bytes, public_key: str = public_key_path.read_text(), algorithm: str = algorithm):
    decoded = jwt.decode(token, public_key, algorithms=[algorithm])
    return decoded


def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()
    pwd_bytes: bytes = password.encode()
    return bcrypt.hashpw(pwd_bytes, salt)


def validate_password(password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(password=password.encode(), hashed_password=hashed_password)
