from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request, Response
from application.helper import endpoint_helper
from sqlalchemy.orm import Session
from application import crud, tasks
from application.setting import settings
from application.logger_config import logger

FILE_NAME = "user:visit"
handle_errors = endpoint_helper.handle_endpoint_errors(FILE_NAME)

router = APIRouter(
    prefix="/visit",
    tags=["Visit Data"]
)

@router.post("/upload")
@handle_errors
async def upload_visit_data(
    request: Request,
    file: UploadFile = File(...),
    hs_unique_code: str = Form(...),
    place_name: str = Form(...),
    person_name: str = Form(...),
    address: str = Form(...),
    person_position: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    description: str = Form(None),
    db: Session = Depends(endpoint_helper.get_db)
):
    user_data = request.state.user
    if not user_data:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user_data["user_id"]

    if not file.filename.lower().endswith((".mp3", ".wav", ".ogg", ".m4a", ".webm")):
        raise HTTPException(status_code=400, detail="Invalid file format")

    user = crud.get_user_by_user_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_bytes = await file.read()

    visit_record = crud.add_new_visit_entry(
        db, user_id, file, hs_unique_code, file_bytes,
        place_name, person_name, address, person_position,
        latitude, longitude, description, file.content_type
    )

    download_url = f"{settings.PUBLIC_URL}/visit/voice/{visit_record.id}"
    msg = (
        f"📍 یک ویزیت جدید ثبت شد!\n"
        f"👨‍💼 کاربر: {user.first_name} {user.last_name}\n"
        f"📧 ایمیل: {user.email}\n"
        f"📱 شماره تماس: {user.phone_number or 'N/A'}\n"
        f"🏢 مکان: {place_name}\n"
        f"👤 شخص: {person_name} ({person_position or 'N/A'})\n"
        f"🧭 طول جغرافیایی & عرض جغرافیایی: {latitude}, {longitude}\n"
        f"🏠 آدرس: {address}\n"
        f"🧾 کد همکاران سیستم: {hs_unique_code}\n"
        f"🎧 دانلود فایل صوتی: {download_url}"
    )
    tasks.report_to_admin_api.delay(msg, message_thread_id=settings.VISITS_THREAD_ID)
    
    # Send voice file directly to Telegram
    tasks.send_voice_to_telegram.delay(visit_record.id)
    
    logger.info(f"{FILE_NAME}:upload_visit_data", extra={"msg_": msg})

    return {
        "message": "Visit data uploaded successfully",
        "id": visit_record.id,
        "filename": visit_record.filename,
        "timestamp": visit_record.visit_timestamp,
    }

@router.get("/voice/{visit_id}")
@handle_errors
async def download_voice(visit_id: int, db: Session = Depends(endpoint_helper.get_db)):
    visit = crud.get_visit_by_visit_id(db, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Voice not found")

    return Response(
        content=visit.file_data,
        media_type=visit.content_type,
        headers={"Content-Disposition": f"attachment; filename={visit.filename}"}
    )