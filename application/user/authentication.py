from fastapi import Request, Depends, Response, APIRouter, HTTPException, Cookie
from fastapi.responses import RedirectResponse
from application import crud, schemas
from application.setting import settings
from sqlalchemy.orm import Session
from application.auth import create_access_token, create_refresh_token, decode_token
from application.database import SessionLocal
from application.logger_config import logger
import random, time
from application.helpers import endpoint_helper, token_helpers

FILE_NAME = "user:authentication"
handle_errors = endpoint_helper.handle_endpoint_errors(FILE_NAME)


router = APIRouter(
    prefix='/auth',
    tags=['authentication']
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()


@router.post('/login')
@handle_errors
async def login(response: Response, data: schemas.VerifyOTPRequirement, db: Session = Depends(get_db)):

    db_user = crud.get_user_by_phone_number(db, data.phone_number)

    if not db_user:
        raise HTTPException(status_code=404, detail="user does not found")
    else:
        user_data = {
            "first_name": db_user.first_name,
            "user_id": db_user.user_id
        }
        access_token = create_access_token(data=user_data)
        cr_refresh_token = create_refresh_token(data=user_data)
        token_helpers.set_cookie(response, "access_token", access_token, settings.ACCESS_TOKEN_EXP_MIN * 60)
        token_helpers.set_cookie(response, "refresh_token", cr_refresh_token, settings.REFRESH_TOKEN_EXP_MIN * 60)

        logger.info(f"{FILE_NAME}:login", extra={"phone_number": data.phone_number, "code": data.code})
        return {'status': 'OK'}

@router.get('/logout-successful')
@handle_errors
async def logout_successful():
    return {'status': 'OK'}


@router.post('/logout')
@handle_errors
async def logout(request: Request):
    redirect = RedirectResponse('/auth/logout-successful', status_code=303)
    blacklist = token_helpers.TokenBlacklist(request.app.state.redis)

    # Access token
    access_token = request.cookies.get("access_token")
    if access_token:
        payload = decode_token(access_token)
        exp = payload.get("exp")
        ttl = max(1, exp - int(time.time())) if exp else settings.ACCESS_TOKEN_EXP_MIN * 60
        await blacklist.add(access_token, ttl)

    # Refresh token
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        payload = decode_token(refresh_token, settings.REFRESH_SECRET_KEY)
        exp = payload.get("exp")
        ttl = max(1, exp - int(time.time())) if exp else settings.REFRESH_TOKEN_EXP_MIN * 60
        await blacklist.add(refresh_token, ttl)

    # Clear cookies
    redirect.delete_cookie(key='access_token', httponly=True, samesite="lax")
    redirect.delete_cookie(key="refresh_token", httponly=True, samesite="lax")
    logger.info(f"{FILE_NAME}:logout")

    request.state.user = None
    return redirect