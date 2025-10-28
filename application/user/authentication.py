from fastapi import Request, Depends, Response, APIRouter, HTTPException, Cookie
from fastapi.responses import RedirectResponse
from application import crud, schemas
from application.setting import settings
from sqlalchemy.orm import Session
from application.auth import create_access_token, create_refresh_token, hash_password_md5, set_cookie
from application.logger_config import logger
from application.helper import endpoint_helper
from application import tasks

FILE_NAME = "user:authentication"
handle_errors = endpoint_helper.handle_endpoint_errors(FILE_NAME)


router = APIRouter(
    prefix='/auth',
    tags=['authentication']
)

@router.post('/login')
@handle_errors
async def login(request: Request, response: Response, data: schemas.LogInRequirement, db: Session = Depends(endpoint_helper.get_db)):
    phone = data.phone_number.strip()
    if not phone.startswith("09") or len(phone) != 11 or not phone.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Invalid phone number. It must start with '09' and contain exactly 11 digits."
        )

    db_user = crud.get_user_by_phone_number(db, data.phone_number)

    if not db_user:
        raise HTTPException(status_code=404, detail="User does not found")
    else:
        hash_password = hash_password_md5(data.password)
        if hash_password != db_user.hashed_password:
            raise HTTPException(status_code=403, detail="Password is not correct")
        user_data = {
            "first_name": db_user.first_name,
            "user_id": db_user.user_id
        }
        access_token = create_access_token(data=user_data)
        cr_refresh_token = create_refresh_token(data=user_data)
        set_cookie(response, "access_token", access_token, settings.ACCESS_TOKEN_EXP_MIN * 60)
        set_cookie(response, "refresh_token", cr_refresh_token, settings.REFRESH_TOKEN_EXP_MIN * 60)

        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        message = (f"🔵 New User Loged In!"
                   f"\n\nUserID: {db_user.user_id}"
                   f"\nFirst Name: {db_user.first_name}"
                   f"\nLast Name: {db_user.last_name}"
                   f"\nPhone Number: {db_user.phone_number}"
                   f"\nClient IP: {client_ip}"
                   f"\nUser Agent: {user_agent}")

        tasks.report_to_admin_api.delay(message, message_thread_id=settings.INFO_THREAD_ID)

        logger.info(f"{FILE_NAME}:login", extra={"phone_number": data.phone_number})
        return {'status': 'OK'}

@router.get('/logout-successful')
@handle_errors
async def logout_successful():
    return {'status': 'OK'}


@router.post('/logout')
@handle_errors
async def logout(request: Request):
    redirect = RedirectResponse('/auth/logout-successful', status_code=303)

    redirect.delete_cookie(key='access_token', httponly=True, samesite="lax")
    redirect.delete_cookie(key="refresh_token", httponly=True, samesite="lax")
    logger.info(f"{FILE_NAME}:logout")

    request.state.user = None
    return redirect