import json
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin

import yaml
from sqlalchemy.orm import Session

from app.models import ApiEndpoint, Project
from app.utils import to_json_text


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def _load_document(content: str) -> Dict[str, Any]:
    try:
        document = json.loads(content)
    except json.JSONDecodeError:
        document = yaml.safe_load(content)
    if not isinstance(document, dict):
        raise ValueError("文档必须是 JSON 或 YAML 对象")
    return document


def _first_success_status(responses: Dict[str, Any]) -> int:
    for key in responses:
        key_text = str(key)
        if key_text.isdigit() and 200 <= int(key_text) < 400:
            return int(key_text)
    return 200


def _schema_example(schema: Dict[str, Any]) -> Any:
    if "example" in schema:
        return schema["example"]
    schema_type = schema.get("type")
    if schema_type == "object":
        return {key: _schema_example(value) for key, value in schema.get("properties", {}).items()}
    if schema_type == "array":
        return [_schema_example(schema.get("items", {}))]
    if schema_type in {"integer", "number"}:
        return 1
    if schema_type == "boolean":
        return True
    return "string"


def _request_body_example(operation: Dict[str, Any]) -> Dict[str, Any]:
    content = operation.get("requestBody", {}).get("content", {})
    media = content.get("application/json") or next(iter(content.values()), {})
    example = media.get("example")
    if isinstance(example, dict):
        return example
    generated = _schema_example(media.get("schema", {}))
    return generated if isinstance(generated, dict) else {}


def _save_endpoint(
    db: Session,
    project_id: int,
    name: str,
    method: str,
    url: str,
    headers: Dict[str, Any],
    body: Dict[str, Any],
    expected_status: int,
) -> Tuple[Optional[int], bool]:
    exists = (
        db.query(ApiEndpoint)
        .filter(ApiEndpoint.project_id == project_id, ApiEndpoint.method == method.upper(), ApiEndpoint.url == url)
        .first()
    )
    if exists:
        return exists.id, False
    endpoint = ApiEndpoint(
        project_id=project_id,
        name=name[:128],
        method=method.upper(),
        url=url,
        headers_json=to_json_text(headers),
        body_json=to_json_text(body),
        expected_status=expected_status,
    )
    db.add(endpoint)
    db.flush()
    return endpoint.id, True


def import_openapi(db: Session, project_id: int, content: str, base_url: str = "") -> Tuple[int, int, List[int]]:
    if db.query(Project).filter(Project.id == project_id).first() is None:
        raise ValueError("项目不存在")
    document = _load_document(content)
    if "openapi" not in document and "swagger" not in document:
        raise ValueError("不是有效的 OpenAPI/Swagger 文档")
    server_url = base_url.strip()
    if not server_url:
        servers = document.get("servers", [])
        if servers:
            server_url = str(servers[0].get("url", ""))
    if not server_url and document.get("swagger"):
        schemes = document.get("schemes") or ["http"]
        server_url = f"{schemes[0]}://{document.get('host', '')}{document.get('basePath', '')}"

    imported = 0
    skipped = 0
    endpoint_ids: List[int] = []
    for path, path_item in document.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            url = urljoin(server_url.rstrip("/") + "/", str(path).lstrip("/")) if server_url else str(path)
            name = operation.get("summary") or operation.get("operationId") or f"{method.upper()} {path}"
            body = _request_body_example(operation)
            endpoint_id, created = _save_endpoint(
                db,
                project_id,
                str(name),
                method,
                url,
                {"Content-Type": "application/json"} if body else {},
                body,
                _first_success_status(operation.get("responses", {})),
            )
            if endpoint_id is not None:
                endpoint_ids.append(endpoint_id)
            if created:
                imported += 1
            else:
                skipped += 1
    db.commit()
    return imported, skipped, endpoint_ids


def _walk_postman_items(items: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    for item in items:
        if isinstance(item.get("item"), list):
            yield from _walk_postman_items(item["item"])
        elif isinstance(item.get("request"), dict):
            yield item


def _postman_url(value: Any, base_url: str) -> str:
    if isinstance(value, str):
        raw = value
    elif isinstance(value, dict):
        raw = value.get("raw") or "/".join(value.get("path", []))
    else:
        raw = ""
    for variable in ("{{baseUrl}}", "{{base_url}}", "{{host}}"):
        raw = raw.replace(variable, base_url.rstrip("/"))
    if base_url and raw.startswith("/"):
        return base_url.rstrip("/") + raw
    return raw


def import_postman(db: Session, project_id: int, content: str, base_url: str = "") -> Tuple[int, int, List[int]]:
    if db.query(Project).filter(Project.id == project_id).first() is None:
        raise ValueError("项目不存在")
    document = _load_document(content)
    if not isinstance(document.get("item"), list):
        raise ValueError("不是有效的 Postman Collection")

    imported = 0
    skipped = 0
    endpoint_ids: List[int] = []
    for item in _walk_postman_items(document["item"]):
        request = item["request"]
        headers = {entry.get("key"): entry.get("value", "") for entry in request.get("header", []) if entry.get("key")}
        body: Dict[str, Any] = {}
        raw_body = request.get("body", {}).get("raw")
        if raw_body:
            try:
                parsed = json.loads(raw_body)
                body = parsed if isinstance(parsed, dict) else {"value": parsed}
            except json.JSONDecodeError:
                body = {"raw": raw_body}
        endpoint_id, created = _save_endpoint(
            db,
            project_id,
            str(item.get("name") or "Postman 接口"),
            str(request.get("method") or "GET"),
            _postman_url(request.get("url"), base_url),
            headers,
            body,
            200,
        )
        if endpoint_id is not None:
            endpoint_ids.append(endpoint_id)
        if created:
            imported += 1
        else:
            skipped += 1
    db.commit()
    return imported, skipped, endpoint_ids
