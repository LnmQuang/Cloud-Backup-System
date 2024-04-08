from datetime import datetime, timedelta
from app.core.mongo_db import database

import jwt


secret_key = "drive_sync_secret_key"


ACCESS_TOKEN_EXPIRE_MINUTES = 600

userData = database.get_collection("usersInfo")


def create_access_token(user_id: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt


def verify_access_token(token: str):
    try:
        decoded_jwt = jwt.decode(token, secret_key, algorithms=["HS256"])
        return decoded_jwt
    except:
        return False


def check_user_exit(id) -> bool:
    user = userData.find_one({"id": id})
    return user is not None
