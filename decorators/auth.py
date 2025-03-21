from functools import wraps
from fastapi import Request
from sqlalchemy.orm import Session

from handlers.exception_handler import APIKeyException

from models import ApiKey


def api_key_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract the request and db objects from kwargs
        request: Request = kwargs.get("request")
        db: Session = kwargs.get("db")
        if not db:
            raise APIKeyException(500, "Database object is missing")
        if not request:
            raise APIKeyException(400, "Request object is missing")

        # Get the Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise APIKeyException(401, "Authorization header missing")

        # Check if the key exists in the database
        api_key = auth_header.replace("Bearer ", "")
        if not get_api_key(db, api_key):
            raise APIKeyException(403, "Invalid Api Key")

        return await func(*args, **kwargs)

    return wrapper


# Get an ApiKey
def get_api_key(db: Session, key: str):
    try:
        api_key = db.query(ApiKey).filter(ApiKey.key == key,
                                          ApiKey.is_active == True,
                                          ApiKey.is_deleted == False).first()
    except Exception as e:
        print(e)
        raise APIKeyException(500, "Internal Server Error")
    if api_key:
        return True
    return False
