from fastapi import APIRouter, Header, HTTPException, Response
from typing import Optional


router = APIRouter(prefix="/demo-target", tags=["内置演示接口"])


@router.post("/login", summary="演示用户登录")
def demo_login(payload: dict, response: Response):
    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    if username == "demo" and password == "123456":
        response.headers["X-Demo-Service"] = "TestPilot"
        return {"token": "demo-token", "username": username}
    raise HTTPException(status_code=401, detail="登录凭据无效")


@router.get("/profile", summary="演示获取用户信息")
def demo_profile(response: Response, authorization: Optional[str] = Header(default=None)):
    if authorization != "Bearer demo-token":
        raise HTTPException(status_code=401, detail="令牌缺失或无效")
    response.headers["X-Demo-Service"] = "TestPilot"
    return {"username": "demo", "role": "tester"}


@router.post("/orders", summary="演示创建订单")
def demo_create_order(payload: dict):
    product_id = payload.get("product_id")
    quantity = payload.get("quantity")
    if not isinstance(product_id, int) or not isinstance(quantity, int):
        raise HTTPException(status_code=400, detail="商品 ID 和数量必须为整数")
    if quantity <= 0 or quantity > 99:
        raise HTTPException(status_code=400, detail="商品数量超出允许范围")
    return {"order_id": 10001, "product_id": product_id, "quantity": quantity}
