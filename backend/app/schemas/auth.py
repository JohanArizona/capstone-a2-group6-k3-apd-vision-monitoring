from pydantic import BaseModel

class LoginRequest(BaseModel):
    """Schema untuk login request"""
    username: str
    password: str

class LoginResponse(BaseModel):
    """Schema untuk login response"""
    access_token: str
    token_type: str = "bearer"
    user: dict
