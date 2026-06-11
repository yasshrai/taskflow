from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    user_id: str
    email: str


class UserLogin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    password: str
