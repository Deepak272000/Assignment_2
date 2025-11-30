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
        "deliveryAddress": order.get("deliveryAddress", ""),
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
        "deliveryAddress": data.deliveryAddress,
        "status": "PENDING",
        "createdAt": datetime.utcnow().isoformat(),
        "updatedAt": datetime.utcnow().isoformat()
    }

    result = orders_collection.insert_one(order)
    order["_id"] = result.inserted_id
    return serialize_order(order)

# @app.get("/orders")
# def list_orders(status: str = None):
#     query = {}
#     if status:
#         query["status"] = status

#     orders = list(orders_collection.find(query))
#     return [serialize_order(o) for o in orders]

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
        {"$set": {"deliveryAddress": data.deliveryAddress, "updatedAt": datetime.utcnow().isoformat()}},
        return_document=True
    )

    if not result:
        raise HTTPException(404, "Order not found!")

    return serialize_order(result)

@app.get("/orders/{orderId}")
def get_order(orderId: str):
    order = orders_collection.find_one({"_id": ObjectId(orderId)})
    if not order:
        raise HTTPException(404, "Order not found!")
    return serialize_order(order)

# Health check
@app.get("/health")
def health():
    return {"status": "ok", "service": "order-service"}

import threading
from .consumer import start_consumer

threading.Thread(target=start_consumer, daemon=True).start()
