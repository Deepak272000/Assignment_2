from pydantic import BaseModel
from typing import List, Dict, Any

class OrderItem(BaseModel):
    productId: str
    quantity: int

class OrderCreate(BaseModel):
    userId: str
    items: List[OrderItem]
    deliveryAddress: str
    email: str

class UpdateStatus(BaseModel):
    status: str

class UpdateEmail(BaseModel):
    email: str

class UpdateAddress(BaseModel):
    deliveryAddress: str
