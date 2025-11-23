from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    postal: str
    
class UserCreate(BaseModel):
    firstName: str
    lastName: str
    email: str
    phone: str
    address : Address

class UpdateEmail(BaseModel):
    email : str

class UpdateAddress(BaseModel):
    address : Address