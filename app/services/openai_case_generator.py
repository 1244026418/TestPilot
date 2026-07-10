import json
from typing import Any, Dict, List, Optional, Tuple

import requests

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from app.services.ai_case_generator import generate_cases


def _extract_json(text: str) -> Dict[str, Any]:
    value = text.strip()
    if value.startswith("```"):
        value = value.split("\n", 1)[-1]
        value = value.rsplit("```", 1)[0]
    return json.loads(value)


def _normalize_cases(raw_cases: List[Dict[str, Any]], headers: Dict[str, Any], body: Dict[str, Any], expected_status: int) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    valid_categories = {"normal", "exception", "boundary", "auth"}
    for index, item in enumerate(raw_cases[:8]):
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "title": str(item.get("title") or f"AI 生成用例 {index + 1}")[:160],
                "category": item.get("category") if item.get("category") in valid_categories else "exception",
                "request_headers": item.get("request_headers") if isinstance(item.get("request_headers"), dict) else headers,
                "request_body": item.get("request_body") if isinstance(item.get("request_body"), dict) else body,
                "expected_status": int(item.get("expected_status") or expected_status),
                "expected_contains": item.get("expected_contains") or None,
                "reason": str(item.get("reason") or "由大模型根据需求和接口信息生成。")[:500],
            }
        )
    if not normalized:
        raise ValueError("AI response did not contain valid cases")
    return normalized


def generate_cases_with_openai(
    requirement: str,
    method: str,
    url: str,
    headers: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    expected_status: int = 200,
) -> List[Dict[str, Any]]:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")
    headers = headers or {}
    body = body or {}
    system_prompt = (
        "你是一名资深接口测试工程师。根据输入生成 4 到 8 条可执行测试用例，覆盖正常、异常、边界和鉴权场景。"
        "只返回 JSON 对象，格式为 "
        '{"cases":[{"title":"","category":"normal|exception|boundary|auth",'
        '"request_headers":{},"request_body":{},"expected_status":200,'
        '"expected_contains":null,"reason":""}]}。不要返回 Markdown。'
    )
    request_body = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "requirement": requirement,
                        "endpoint": {
                            "method": method.upper(),
                            "url": url,
                            "headers": headers,
                            "body": body,
                            "normal_expected_status": expected_status,
                        },
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    endpoint = OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
    response = requests.post(
        endpoint,
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
        json=request_body,
        timeout=45,
    )
    if response.status_code >= 400 and response.status_code in {400, 404, 422}:
        request_body.pop("response_format", None)
        response = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json=request_body,
            timeout=45,
        )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    parsed = _extract_json(content)
    raw_cases = parsed.get("cases", [])
    if not isinstance(raw_cases, list):
        raise ValueError("AI response cases must be a list")
    return _normalize_cases(raw_cases, headers, body, expected_status)


def generate_cases_smart(
    requirement: str,
    method: str,
    url: str,
    headers: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    expected_status: int = 200,
    use_ai: bool = True,
) -> Tuple[List[Dict[str, Any]], str, str]:
    if use_ai and OPENAI_API_KEY:
        try:
            cases = generate_cases_with_openai(requirement, method, url, headers, body, expected_status)
            return cases, "openai", "已使用 GPT 生成测试用例"
        except Exception as exc:
            fallback = generate_cases(requirement, method, url, headers, body, expected_status)
            return fallback, "rules", f"GPT 调用失败，已回退规则生成器：{exc}"
    fallback = generate_cases(requirement, method, url, headers, body, expected_status)
    message = "未配置 OpenAI API，已使用规则生成器" if use_ai else "已使用规则生成器"
    return fallback, "rules", message
