from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import jwt
from application.logger_config import fastapi_listener
from application.auth import create_access_token, set_cookie
from application.setting import settings
from application.user import authentication, visit
from application.admin import manage, init
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    fastapi_listener.start()
    yield
    fastapi_listener.stop()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# templates = Jinja2Templates(directory="templates")
# application.mount('/statics', StaticFiles(directory='statics'), name='static')

app.include_router(authentication.router)
app.include_router(manage.router)
app.include_router(init.router)
app.include_router(visit.router)

@app.middleware("http")
async def authenticate_request(request: Request, call_next):

    exception_paths = ["/auth/logout-successful", "/auth/login", "/docs", "/auth/logout", "/admin/init"]

    if any(request.url.path.startswith(path) for path in exception_paths):
        return await call_next(request)

    request.state.user = None
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    if access_token:
        try:
            payload = jwt.decode(access_token, settings.ACCESS_TOKEN_SECRET_KEY, algorithms=settings.ALGORITHM)
            request.state.user = payload
            return await call_next(request)
        except jwt.ExpiredSignatureError:
            pass
        except jwt.InvalidTokenError:
            return JSONResponse(status_code=401, content={"detail": "Invalid access token"})

    if refresh_token:
        try:
            refresh_payload = jwt.decode(refresh_token, settings.REFRESH_TOKEN_SECRET_KEY, algorithms=settings.ALGORITHM)
            new_token = create_access_token({
                "user_id": refresh_payload["user_id"],
                "first_name": refresh_payload["first_name"]
            })

            request.state.user = jwt.decode(new_token, settings.ACCESS_TOKEN_SECRET_KEY, algorithms=["HS256"])
            response = await call_next(request)
            set_cookie(response, "access_token", new_token, settings.ACCESS_TOKEN_EXP_MIN * 60)
            return response
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return JSONResponse(status_code=401, content={"detail": "Invalid or expierd refresh token"})

    return JSONResponse(status_code=401, content={"detail": "Unauthorized: No token found"})
