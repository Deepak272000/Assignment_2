from fastapi import HTTPException, FastAPI
from .database import users_collection
from .schemas import UserCreate, UpdateAddress, UpdateEmail
from bson import ObjectId
from datetime import datetime
from .publisher import publish_user_updated

app = FastAPI (title="User service v2", version = "2.0")

#serializer:
def serialize_user(user):
    return{
        "userId" : str(user["_id"]),
        "firstName" : user["firstName"],
        "lastName" : user["lastName"],
        "email" : user["email"],
        "phone" : user["phone"],
        "address": {
            "street": user["address"].get("street"),
            "city": user["address"].get("city"),
            "postal": user["address"].get("postal")
        },
        "createdAt" : user["createdAt"],
        "updatedAt" : user["updatedAt"]
    }

#create users:
@app.post("/users")
def create_user(data: UserCreate):
    user = {
        "firstName": data.firstName,
        "lastName": data.lastName,
        "email": data.email,
        "phone": data.phone,
        "address": {
            "street": data.address.street,
            "city": data.address.city,
            "postal": data.address.postal
        },
        "createdAt": datetime.utcnow().isoformat(),
        "updatedAt": datetime.utcnow().isoformat()
    }

    result = users_collection.insert_one(user)
    user["_id"] = result.inserted_id
    return serialize_user(user)

#now let's updte email:
@app.put("/users/{userId}/email")
def update_email(userId: str, data: UpdateEmail):
    result = users_collection.find_one_and_update(
        {"_id": ObjectId(userId)},
        {"$set": {"email": data.email, "updatedAt": datetime.utcnow().isoformat()}},
        return_document= True
    )
    if not result:
        raise HTTPException(status_code=404, detail="User Not Found!")
    event = {
        "type": "UserUpdated",
        "userId": str(result["_id"]),
        "email": data.email,
        "address": result["address"]
    }

    publish_user_updated(event)

    return serialize_user(result)

#now I will update address for user:
@app.put("/users/{userId}/address")
def update_address(userId:str, data:UpdateAddress):
    new_address = {
        "street": data.address.street,
        "city": data.address.city,
        "postal": data.address.postal
    }
    result = users_collection.find_one_and_update(
        {"_id": ObjectId(userId)},
        {"$set": {"address": new_address, "updatedAt": datetime.utcnow().isoformat()}},
        return_document= True
    )
    if not result:
        raise HTTPException(status_code=404, detail="User Not Found!")
    event = {
        "type": "UserUpdated",
        "userId": str(result["_id"]),
        "email": result["email"],
        "address": new_address
    }

    publish_user_updated(event)

    return serialize_user(result)