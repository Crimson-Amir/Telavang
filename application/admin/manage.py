from fastapi import APIRouter, Depends, HTTPException, Request
from application import crud, schemas
from sqlalchemy.orm import Session
from application.helper import endpoint_helper
from application.logger_config import logger
from application.setting import settings
from application import tasks

FILE_NAME = 'admin:manage'
handle_errors = endpoint_helper.handle_endpoint_errors(FILE_NAME)

router = APIRouter(
    prefix='/admin',
    tags=['hardware_communication']
)

def require_admin(
    request: Request,
    db: Session = Depends(endpoint_helper.get_db)
):
    user = request.state.user
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    is_admin = crud.is_user_admin(db, user_id)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access only")

    return is_admin

@router.post('/new_admin', response_model=schemas.NewAdminResult)
@handle_errors
async def new_admin(admin: schemas.NewAdminRequirement, db: Session = Depends(endpoint_helper.get_db), is_admin = Depends(require_admin)):
    new = crud.register_new_admin(db, admin.user_id, admin.status)
    message = (f"🔵 New Admin Registered!"
               f"\n\nUserID: {admin.user_id}"
               f"\nAdminID: {new.admin_id}"
               f"\nAdmin Status: {admin.status}"
               f"\n\n- Removed by Admin With ID {is_admin.admin_id}")

    tasks.report_to_admin_api.delay(message, message_thread_id=settings.INFO_THREAD_ID)
    logger.info(f"{FILE_NAME}:new_admin", extra={"msg_": message})
    return new

@router.delete('/remove_admin/{admin_id}')
@handle_errors
async def remove_admin(admin_id: int, db: Session = Depends(endpoint_helper.get_db), is_admin= Depends(require_admin)):
    result = crud.remove_admin(db, admin_id)
    if result:
        message = (f"🔵 Admin Removed!"
                   f"\nAdminID: {admin_id}"
                   f"\n\n- Removed by Admin With ID {is_admin.admin_id}")
        logger.info(f"{FILE_NAME}:remove_admin", extra={"msg_": message})
        tasks.report_to_admin_api.delay(message, message_thread_id=settings.INFO_THREAD_ID)
        return {"status": "admin removed!"}

    raise HTTPException(
        status_code=404,
        detail="Admin ID does not exist"
    )


@router.post('/create_user/')
@handle_errors
async def create_user(user: schemas.SignUpRequirement, request: Request, db: Session = Depends(endpoint_helper.get_db), is_admin= Depends(require_admin)):

    db_user = crud.get_user_by_phone_number(db, user.phone_number)
    if db_user: raise HTTPException(status_code=400, detail="this user already exists!")

    create_user_db = crud.create_user(db, user)

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    extra = {"phone_number": user.phone_number, "first_name": user.first_name,
              'last_name': user.last_name, 'user_id': create_user_db.user_id, 'password': user.password,
              "ip_address": client_ip, "user_agent": user_agent, "admin_id": is_admin.admin_id}

    logger.info(f"{FILE_NAME}:create_user", extra=extra)
    msg = "👤 New User Registered!\n"

    for key, value in extra.items():
        msg += f"\n{key}: {value}"

    tasks.report_to_admin_api.delay(msg, message_thread_id=settings.NEW_USER_THREAD_ID)

    return {'msg': 'user created', 'user_id': create_user_db.user_id}
