import os
import json
import random
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="API Gateway", version="1.0")

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


# USER (V1/V2 ROUTING)
# STRANGLER PATTERN
@app.get("/users")
async def gateway_users_info():
    return {
        "message": "User endpoint gateway. POST/PUT/GET will be forwarded internally.",
        "routing_percentage_v1": USER_V1_PERCENT,
        "v1_base_url": USER_V1_URL,
        "v2_base_url": USER_V2_URL
    }

@app.get("/orders")
async def gateway_orders_info():
    return {
        "message": "Order endpoint gateway. All requests forwarded to order service.",
        "order_service_url": ORDER_URL
    }


# Real routing endpoints (hidden from Swagger)
@app.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], include_in_schema=False)
async def route_user(path: str, request: Request):

    random_number = random.randint(0, 99)

    if random_number < USER_V1_PERCENT:
        forward_to = f"{USER_V1_URL}/users/{path}"
    else:
        forward_to = f"{USER_V2_URL}/users/{path}"

    return await forward_request(request, forward_to)


@app.api_route("/orders/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], include_in_schema=False)
async def route_order(path: str, request: Request):
    forward_to = f"{ORDER_URL}/orders/{path}"
    return await forward_request(request, forward_to)


# Health check FOR AWS

@app.get("/health")
async def health():
    return {"status": "ok"}
