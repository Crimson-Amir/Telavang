import functools, requests
from celery import Celery
from application.logger_config import celery_logger
from application.database import SessionLocal
from application.setting import settings
import traceback
from uuid import uuid4
from contextlib import contextmanager

celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=None
)

@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5})
def report_to_admin_api(msg, message_thread_id=settings.ERR_THREAD_ID, reply_markup=None):
    json_data = {'chat_id': settings.TELEGRAM_CHAT_ID, 'text': msg[:4096], 'message_thread_id': message_thread_id}
    if reply_markup:
        json_data['reply_markup'] = reply_markup
    response = requests.post(
        url=f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendMessage",
        json=json_data,
        timeout=10
    )
    response.raise_for_status()

@celery_app.task(autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5})
def send_voice_to_telegram(visit_id: int):
    """Send voice file to Telegram chat/thread"""
    from application import crud
    import io
    
    with session_scope() as db:
        visit_record = crud.get_visit_by_visit_id(db, visit_id)
        if not visit_record:
            celery_logger.error(f"Visit record {visit_id} not found")
            return
        
        # Prepare the voice file
        voice_file = io.BytesIO(visit_record.file_data)
        voice_file.name = visit_record.filename
        
        # Send voice to Telegram
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendVoice"
        files = {'voice': (visit_record.filename, voice_file, visit_record.content_type)}
        data = {
            'chat_id': settings.TELEGRAM_CHAT_ID,
            'message_thread_id': settings.VISITS_THREAD_ID,
            'caption': (
                f"🎧 فایل صوتی\n"
            )
        }
        
        response = requests.post(url, files=files, data=data, timeout=30)
        response.raise_for_status()
        celery_logger.info(f"Voice file sent to Telegram for visit_id: {visit_id}")

def handle_task_errors(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            retries = getattr(self.request, "retries", None)
            max_retries = getattr(self, "max_retries", None)
            error_id = uuid4().hex
            tb = traceback.format_exc()

            celery_logger.error(
                f"Celery task {func.__name__} failed",
                extra={"error": str(e), "traceback": tb},
            )

            err_msg = (
                f"[🔴 ERROR] Celery task: {func.__name__}"
                f"\n\nType: {type(e)}"
                f"\nReason: {str(e)}"
                f"\nRetries: {retries}/{max_retries}"
                f"\nError ID: {error_id}"
            )

            report_to_admin_api.delay(err_msg)
            raise
    return wrapper