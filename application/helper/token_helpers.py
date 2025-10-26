import hashlib, datetime
from application import crud
from application.database import SessionLocal
import logging

logging.getLogger("application")
bakery_token = {}

def get_expiry(minutes=10):
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=minutes)

def get_token(bakery_id):
    if bakery_id not in bakery_token:
        db = SessionLocal()
        try:
            bakery = crud.get_bakery(db, bakery_id)
            if not bakery:
                raise ValueError('No bakery found')
            bakery_token[bakery_id] = bakery.token
        finally:
            db.close()
    return bakery_token[bakery_id]


def set_cookie(response, key, value, max_age):
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=False, # TODO: TRUE FOR HTTPS
        samesite="lax",
        max_age=max_age
    )