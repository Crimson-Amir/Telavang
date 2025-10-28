from pydantic import BaseModel

class SignUpRequirement(BaseModel):
    phone_number: str
    email: str
    first_name: str
    last_name: str
    password: str
    active: bool

class UserID(BaseModel):
    user_id: int

class AdminID(BaseModel):
    admin_id: int

class SignUpReturn(UserID):
    pass

class LogInRequirement(BaseModel):
    phone_number: str
    password: str


class NewAdminRequirement(UserID):
    status: bool = True

class NewAdminResult(BaseModel):
    admin_id: int

    class Config:
        from_attributes = True
