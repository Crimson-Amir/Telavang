from sqlalchemy.orm import Session
from application import models, schemas
from application.auth import hash_password_md5

def get_user_by_phone_number(db: Session, phone_number: str):
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()

def is_user_admin(db: Session, user_id: str):
    return db.query(models.Admin).filter_by(user_id=user_id, active=True).first()

def create_user(db: Session, user: schemas.SignUpRequirement):
    hash_password = hash_password_md5(user.password)
    db_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        hashed_password=hash_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def register_new_admin(db: Session, admin: schemas.NewAdminRequirement):
    new_admin = models.Admin(user_id=admin.user_id, active=admin.status)
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin