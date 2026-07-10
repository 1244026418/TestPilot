from copy import deepcopy
from typing import Any, Dict, List, Optional


def _first_key(data: Dict[str, Any]) -> Optional[str]:
    for key in data:
        return key
    return None


def _mutate_boundary_value(value: Any) -> Any:
    if isinstance(value, (int, float)):
        return -1
    if isinstance(value, str):
        return value + "x" * 128
    if isinstance(value, bool):
        return not value
    if isinstance(value, list):
        return []
    if isinstance(value, dict):
        return {}
    return None


def generate_cases(
    requirement: str,
    method: str,
    url: str,
    headers: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    expected_status: int = 200,
) -> List[Dict[str, Any]]:
    """Generate interview-friendly API test cases without requiring an LLM key."""
    headers = headers or {}
    body = body or {}
    requirement_lower = requirement.lower()
    cases: List[Dict[str, Any]] = [
        {
            "title": "正常流程：参数合法时接口返回成功",
            "category": "normal",
            "request_headers": headers,
            "request_body": body,
            "expected_status": expected_status,
            "expected_contains": None,
            "reason": "覆盖接口主流程，确认核心业务路径可用。",
        }
    ]

    required_key = _first_key(body)
    if required_key:
        missing_body = deepcopy(body)
        missing_body.pop(required_key, None)
        cases.append(
            {
                "title": f"异常流程：缺少必填参数 {required_key}",
                "category": "exception",
                "request_headers": headers,
                "request_body": missing_body,
                "expected_status": 400,
                "expected_contains": None,
                "reason": "覆盖必填参数校验，避免后端直接处理脏数据。",
            }
        )

        boundary_body = deepcopy(body)
        boundary_body[required_key] = _mutate_boundary_value(body[required_key])
        cases.append(
            {
                "title": f"边界流程：{required_key} 使用异常边界值",
                "category": "boundary",
                "request_headers": headers,
                "request_body": boundary_body,
                "expected_status": 400,
                "expected_contains": None,
                "reason": "覆盖边界值与类型异常，验证接口参数防御能力。",
            }
        )

    if "登录" in requirement or "login" in requirement_lower or "token" in requirement_lower:
        bad_login = deepcopy(body) or {"username": "wrong", "password": "wrong"}
        if "password" in bad_login:
            bad_login["password"] = "wrong-password"
        cases.append(
            {
                "title": "异常流程：账号或密码错误时拒绝登录",
                "category": "auth",
                "request_headers": headers,
                "request_body": bad_login,
                "expected_status": 401,
                "expected_contains": None,
                "reason": "登录接口必须验证身份，不能把错误凭据当作成功请求。",
            }
        )

    if "鉴权" in requirement or "权限" in requirement or "auth" in requirement_lower:
        no_auth_headers = {k: v for k, v in headers.items() if k.lower() != "authorization"}
        cases.append(
            {
                "title": "鉴权流程：缺少 Authorization 时返回未授权",
                "category": "auth",
                "request_headers": no_auth_headers,
                "request_body": body,
                "expected_status": 401,
                "expected_contains": None,
                "reason": "覆盖未登录访问受保护接口的安全边界。",
            }
        )

    if "分页" in requirement or "page" in requirement_lower:
        page_body = deepcopy(body)
        page_body.update({"page": 0, "page_size": 5000})
        cases.append(
            {
                "title": "边界流程：分页参数越界时返回参数错误",
                "category": "boundary",
                "request_headers": headers,
                "request_body": page_body,
                "expected_status": 400,
                "expected_contains": None,
                "reason": "分页参数是接口测试高频追问点，需验证最小页码和最大页大小。",
            }
        )

    return cases[:6]
