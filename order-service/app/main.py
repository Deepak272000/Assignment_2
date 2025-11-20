from fastapi import FastAPI, HTTPException
from bson import ObjectId
from datetime import datetime
from .database import orders_collection
from .schemas import OrderCreate, UpdateStatus, UpdateEmail, UpdateAddress, OrderItem

app = FastAPI(title="Order Service v1", version="1.0")


def serialize_order(order):
    return {
        "orderId": str(order["_id"]),
        "userId": order["userId"],
        "items": order["items"],
        "email": order["email"],
        "deliveryAddress": order["deliveryAddress"],
        "status": order["status"],
        "createdAt": order["createdAt"],
        "updatedAt": order["updatedAt"]
    }


@app.post("/orders")
def create_order(data: OrderCreate):
    order = {
        "userId": data.userId,
        "items": [item.dict() for item in data.items],
        "email": data.email,
        "addrdeliveryAddressess": data.deliveryAddress,
        "status": "PENDING",
        "createdAt": datetime.utcnow().isoformat(),
        "updatedAt": datetime.utcnow().isoformat()
    }

    result = orders_collection.insert_one(order)
    order["_id"] = result.inserted_id
    return serialize_order(order)

@app.get("/orders")
def list_orders(status: str = None):
    query = {}
    if status:
        query["status"] = status

    orders = list(orders_collection.find(query))
    return [serialize_order(o) for o in orders]

@app.put("/orders/{orderId}/status")
def update_status(orderId: str, data: UpdateStatus):
    result = orders_collection.find_one_and_update(
        {"_id": ObjectId(orderId)},
        {"$set": {"status": data.status, "updatedAt": datetime.utcnow().isoformat()}},
        return_document=True
    )

    if not result:
        raise HTTPException(404, "Order not found")

    return serialize_order(result)

@app.put("/orders/{orderId}/email")
def update_email(orderId: str, data: UpdateEmail):
    result = orders_collection.find_one_and_update(
        {"_id": ObjectId(orderId)},
        {"$set": {"email": data.email, "updatedAt": datetime.utcnow().isoformat()}},
        return_document=True
    )

    if not result:
        raise HTTPException(404, "Order not found")

    return serialize_order(result)

@app.put("/orders/{orderId}/address")
def update_address(orderId: str, data: UpdateAddress):
    result = orders_collection.find_one_and_update(
        {"_id": ObjectId(orderId)},
        {"$set": {"address": data.address, "updatedAt": datetime.utcnow().isoformat()}},
        return_document=True
    )

    if not result:
        raise HTTPException(404, "Order not found!")

    return serialize_order(result)
