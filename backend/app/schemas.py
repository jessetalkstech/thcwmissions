from pydantic import BaseModel
from typing import List, Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    points: int
    class Config:
        from_attributes = True

class MissionBase(BaseModel):
    title: str
    description: Optional[str] = None
    base_points: int = 0

class MissionRead(MissionBase):
    id: int
    class Config:
        from_attributes = True

class ObjectiveBase(BaseModel):
    description: str
    order_index: int

class ObjectiveCreate(ObjectiveBase):
    pass

class ObjectiveRead(ObjectiveBase):
    id: int
    mission_id: int
    is_completed: bool

    class Config:
        from_attributes = True

class HarvestBase(BaseModel):
    extracted_data: dict
    status: str

class HarvestUpdate(BaseModel):
    extracted_data: Optional[dict] = None

class HarvestRead(HarvestBase):
    id: int
    user_id: int
    image_url: str

    class Config:
        from_attributes = True

class UserMission(BaseModel):
    id: int
    user_id: int
    mission_id: int
    current_objective_id: int
    status: str

    class Config:
        from_attributes = True
