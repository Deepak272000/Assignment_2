from pydantic import BaseModel

class UserCreate(BaseModel):
    email : str
    deliveryAddress : str

class UpdateEmail(BaseModel):
    email : str

class UpdateAddress(BaseModel):
    deliveryAddress : str