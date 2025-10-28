from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from application import crud, schemas
from application.helper import endpoint_helper

FILE_NAME = 'admin:init'
handle_errors = endpoint_helper.handle_endpoint_errors(FILE_NAME)

router = APIRouter(
    prefix='/admin_init',
    tags=['admin init']
)

@router.post("/init")
async def init_admin(
    admin: schemas.SignUpRequirement,
    db: Session = Depends(endpoint_helper.get_db)
):
    existing_admin = crud.get_first_admin(db)
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists")
    user = crud.create_user(db, admin)
    admin = crud.create_admin(db, user.user_id)

    return {"message": "Admin initialized successfully", "admin_id": admin.admin_id}
