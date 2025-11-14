from fastapi import HTTPException, FastAPI
from .database import users_collection
from .schemas import UserCreate, UpdateAddress, UpdateEmail
from bson import objectid
from datetime import datetime

app = FastAPI (title="User service v1", version = "1.0")

#serializer:
def serialize_user(user):
    return{
        "userId" : str(user["_id"]),
        "email" : user["email"],
        "deliveryAddress" : user["deliveryAddress"],
        "createdAt" : user["createdAt"],
        "updatedAt" : user["updatedAt"]
    }

#create users:
@app.post("/users")
def create_user(data: UserCreate):
    user = {
        "email":data.email,
        "deliveryAddress":data.deliveryAddress,
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
        {"_Id": objectid(userId)},
        {"$set": {"email": data.email, "updatedAt": datetime.utcnow().isoformat()}},
        return_document= True
    )
    if not result:
        raise HTTPException(status_code=404, detail="User Not Found!")
    return serialize_user(result)

#now I will update address for user:
@app.put("/users/({userId})/address")
def update_address(userId:str, data:UpdateAddress):
    result = users_collection.find_one_and_update(
        {"_Id": objectid(userId)},
        {"$set": {"deliveryAddress": data.deliveryAddress, "updatedAt": datetime.utcnow().isoformat()}},
        return_document= True
    )
    if not result:
        raise HTTPException(status_code=404, detail="User Not Found!")
    return serialize_user(result)