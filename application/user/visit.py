from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request
from application.auth import decode_token
from application.helper import endpoint_helper
from sqlalchemy.orm import Session
from application import crud

FILE_NAME = "user:visit"
handle_errors = endpoint_helper.handle_endpoint_errors(FILE_NAME)

router = APIRouter(
    prefix="/visit",
    tags=["Visit Data"]
)

@router.post("/upload")
async def upload_visit_data(
    request: Request,
    file: UploadFile = File(...),
    hs_unique_code: str = Form(...),
    place_name: str = Form(...),
    person_name: str = Form(...),
    person_position: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    description: str = Form(None),
    db: Session = Depends(endpoint_helper.get_db)
):
    access_token = request.cookies.get('access_token')
    data = decode_token(access_token)
    user_id = data['user_id']

    if not file.filename.lower().endswith((".mp3", ".wav", ".ogg", ".m4a")):
        raise HTTPException(status_code=400, detail="Invalid file format")

    user = crud.get_user_by_user_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_bytes = await file.read()

    visit_record = crud.add_new_visit_entry(
        db, user_id, file, hs_unique_code, file_bytes,
        place_name, person_name, person_position,
        latitude, longitude, description
    )

    return {
        "message": "Visit data uploaded successfully",
        "id": visit_record.id,
        "filename": visit_record.filename,
        "timestamp": visit_record.visit_timestamp,
    }