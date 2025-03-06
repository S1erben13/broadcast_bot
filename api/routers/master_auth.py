from fastapi import APIRouter
from fastapi.params import Depends
import auth.utils as auth_utils
from schemas import Master, Token

router = APIRouter(prefix='/auth', tags=['auth'])


def validate_auth_master():
    pass


@router.post('/login')
async def auth_master_jwt(master: Master = Depends(validate_auth_master)):
    jwt_payload = {"sub": master.user_id, "role": master.role}
    token = auth_utils.encode_jwt(jwt_payload)
    return Token(access_token=token, token_type="Bearer")
