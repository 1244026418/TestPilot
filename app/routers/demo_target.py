from fastapi import APIRouter, Header, HTTPException
from typing import Optional


router = APIRouter(prefix="/demo-target", tags=["demo target"])


@router.post("/login")
def demo_login(payload: dict):
    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password are required")
    if username == "demo" and password == "123456":
        return {"token": "demo-token", "username": username}
    raise HTTPException(status_code=401, detail="invalid credentials")


@router.get("/profile")
def demo_profile(authorization: Optional[str] = Header(default=None)):
    if authorization != "Bearer demo-token":
        raise HTTPException(status_code=401, detail="missing or invalid token")
    return {"username": "demo", "role": "tester"}


@router.post("/orders")
def demo_create_order(payload: dict):
    product_id = payload.get("product_id")
    quantity = payload.get("quantity")
    if not isinstance(product_id, int) or not isinstance(quantity, int):
        raise HTTPException(status_code=400, detail="product_id and quantity must be integers")
    if quantity <= 0 or quantity > 99:
        raise HTTPException(status_code=400, detail="quantity out of range")
    return {"order_id": 10001, "product_id": product_id, "quantity": quantity}
