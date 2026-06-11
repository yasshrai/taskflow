from pydantic import BaseModel, ConfigDict


class LeaderCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: str
    password: str


class LeaderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    leader_id: str
    name: str
    email: str


class LeaderLogin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    password: str
