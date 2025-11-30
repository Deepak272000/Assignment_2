import os
import json
import random
import httpx
from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="E-Commerce API Gateway",
    version="1.0",
    description="Gateway for User Services (V1 & V2) and Order Service with Strangler Pattern (70% V1, 30% V2)"
)

# -----------------------------
# Load configuration
# -----------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "gateway-config.json")

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)


USER_V1_PERCENT = config["user_v1_percentage"]
USER_V1_URL = config["user_v1_url"]
USER_V2_URL = config["user_v2_url"]
ORDER_URL = config["order_url"]

# -----------------------------
# Schemas
# -----------------------------

# User V1 Schemas
class UserCreateV1(BaseModel):
    email: str
    deliveryAddress: str

class UpdateEmailV1(BaseModel):
    email: str

class UpdateAddressV1(BaseModel):
    deliveryAddress: str

# User V2 Schemas
class AddressV2(BaseModel):
    street: str
    city: str
    postal: str

class UserCreateV2(BaseModel):
    firstName: str
    lastName: str
    email: str
    phone: str
    address: AddressV2

class UpdateEmailV2(BaseModel):
    email: str

class UpdateAddressV2(BaseModel):
    address: AddressV2

# Order Schemas
class OrderItem(BaseModel):
    productId: str
    quantity: int

class OrderCreate(BaseModel):
    userId: str
    items: List[OrderItem]
    email: str
    deliveryAddress: str

class UpdateStatus(BaseModel):
    status: str

class UpdateOrderEmail(BaseModel):
    email: str

class UpdateOrderAddress(BaseModel):
    deliveryAddress: str

# Helper to forward request
async def forward_request(request: Request, target_url: str):
    async with httpx.AsyncClient() as client:
        method = request.method
        body = await request.body()
        headers = dict(request.headers)

        try:
            response = await client.request(
                method,
                target_url,
                content=body,
                headers=headers
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"Gateway could not reach microservice: {str(e)}"}
            )

        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=response.headers
        )


# =============================================================================
# USER SERVICE V1 ENDPOINTS (70% traffic via Strangler Pattern)
# =============================================================================

@app.post("/users/v1", tags=["User Service V1"], summary="Create User (V1 Schema)")
async def create_user_v1(user: UserCreateV1):
    """Create a new user using V1 schema (simple: email + deliveryAddress)"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_V1_URL}/users", json=user.dict())
        return response.json()

@app.put("/users/v1/{userId}/email", tags=["User Service V1"], summary="Update User Email (V1)")
async def update_user_email_v1(userId: str, data: UpdateEmailV1):
    """Update user email in V1 service"""
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{USER_V1_URL}/users/{userId}/email", json=data.dict())
        return response.json()

@app.put("/users/v1/{userId}/address", tags=["User Service V1"], summary="Update User Address (V1)")
async def update_user_address_v1(userId: str, data: UpdateAddressV1):
    """Update user delivery address in V1 service"""
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{USER_V1_URL}/users/{userId}/address", json=data.dict())
        return response.json()

@app.get("/users/v1/{userId}", tags=["User Service V1"], summary="Get User by ID (V1)")
async def get_user_v1(userId: str):
    """Get user details by userId from V1 service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_V1_URL}/users/{userId}")
        return response.json()

# =============================================================================
# USER SERVICE V2 ENDPOINTS (30% traffic via Strangler Pattern)
# =============================================================================

@app.post("/users/v2", tags=["User Service V2"], summary="Create User (V2 Schema)")
async def create_user_v2(user: UserCreateV2):
    """Create a new user using V2 schema (enhanced: firstName, lastName, phone, structured address)"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_V2_URL}/users", json=user.dict())
        return response.json()

@app.put("/users/v2/{userId}/email", tags=["User Service V2"], summary="Update User Email (V2)")
async def update_user_email_v2(userId: str, data: UpdateEmailV2):
    """Update user email in V2 service"""
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{USER_V2_URL}/users/{userId}/email", json=data.dict())
        return response.json()

@app.put("/users/v2/{userId}/address", tags=["User Service V2"], summary="Update User Address (V2)")
async def update_user_address_v2(userId: str, data: UpdateAddressV2):
    """Update user address in V2 service (structured: street, city, postal)"""
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{USER_V2_URL}/users/{userId}/address", json=data.dict())
        return response.json()

@app.get("/users/v2/{userId}", tags=["User Service V2"], summary="Get User by ID (V2)")
async def get_user_v2(userId: str):
    """Get user details by userId from V2 service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_V2_URL}/users/{userId}")
        return response.json()

# =============================================================================
# USER SERVICE - AUTO ROUTING (Strangler Pattern: 70% V1, 30% V2)
# =============================================================================

@app.post("/users", tags=["User Auto-Routing"], summary="Create User (Auto-routed to V1 or V2)")
async def create_user_auto(request: Request):
    """
    Creates a user with automatic routing based on Strangler Pattern:
    - 70% traffic goes to User Service V1
    - 30% traffic goes to User Service V2
    
    Use /users/v1 or /users/v2 for explicit version routing.
    """
    random_number = random.randint(0, 99)
    body = await request.body()
    
    if random_number < USER_V1_PERCENT:
        forward_to = f"{USER_V1_URL}/users"
        version = "V1"
    else:
        forward_to = f"{USER_V2_URL}/users"
        version = "V2"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(forward_to, content=body, headers=dict(request.headers))
        result = response.json()
        result["routed_to"] = version
        return result

# =============================================================================
# ORDER SERVICE ENDPOINTS
# =============================================================================

@app.post("/orders", tags=["Order Service"], summary="Create Order")
async def create_order(order: OrderCreate):
    """Create a new order"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{ORDER_URL}/orders", json=order.dict())
        return response.json()

@app.get("/orders", tags=["Order Service"], summary="List Orders")
async def list_orders(status: Optional[str] = None):
    """List all orders, optionally filter by status (PENDING, COMPLETED, etc.)"""
    async with httpx.AsyncClient() as client:
        params = {"status": status} if status else {}
        response = await client.get(f"{ORDER_URL}/orders", params=params)
        return response.json()

@app.put("/orders/{orderId}/status", tags=["Order Service"], summary="Update Order Status")
async def update_order_status(orderId: str, data: UpdateStatus):
    """Update order status (PENDING, PROCESSING, SHIPPED, DELIVERED, CANCELLED)"""
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{ORDER_URL}/orders/{orderId}/status", json=data.dict())
        return response.json()

@app.put("/orders/{orderId}/email", tags=["Order Service"], summary="Update Order Email")
async def update_order_email(orderId: str, data: UpdateOrderEmail):
    """Update email for an order"""
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{ORDER_URL}/orders/{orderId}/email", json=data.dict())
        return response.json()

@app.put("/orders/{orderId}/address", tags=["Order Service"], summary="Update Order Delivery Address")
async def update_order_address(orderId: str, data: UpdateOrderAddress):
    """Update delivery address for an order"""
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{ORDER_URL}/orders/{orderId}/address", json=data.dict())
        return response.json()

@app.get("/orders/{orderId}", tags=["Order Service"], summary="Get Order by ID")
async def get_order(orderId: str):
    """Get order details by orderId"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ORDER_URL}/orders/{orderId}")
        return response.json()


# Health check FOR AWS

@app.get("/health")
async def health():
    return {"status": "ok"}
