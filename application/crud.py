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

def remove_admin(db: Session, admin_id: int):
    admin = db.query(models.Admin).filter(models.Admin.id == admin_id).first()
    if not admin:
        return None
    db.delete(admin)
    db.commit()
    return True

def get_user_by_user_id(db: Session, user_id: int):
    return db.query(models.User).filter_by(user_id=user_id, active=True).first()

def add_new_visit_entry(
        db: Session, user_id: int, file, hs_unique_code: str, file_bytes,
        place_name: str, person_name: str, person_position: str,
        latitude: float, longitude: float, description: str
):

    visit_record = models.VisitData(
        user_id=user_id,
        hs_unique_code=hs_unique_code,
        filename=file.filename,
        file_data=file_bytes,
        place_name=place_name,
        person_name=person_name,
        person_position=person_position,
        latitude=latitude,
        longitude=longitude,
        description=description,
    )

    db.add(visit_record)
    db.commit()
    db.refresh(visit_record)

    return visit_record

