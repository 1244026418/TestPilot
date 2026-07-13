import re
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from jsonpath_ng.ext import parse as parse_jsonpath
from jsonpath_ng.exceptions import JSONPathError
from jsonschema import ValidationError, validate


VARIABLE_PATTERN = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*}}")


def interpolate(value: Any, variables: Mapping[str, Any]) -> Any:
    if isinstance(value, dict):
        return {key: interpolate(item, variables) for key, item in value.items()}
    if isinstance(value, list):
        return [interpolate(item, variables) for item in value]
    if not isinstance(value, str):
        return value

    full_match = VARIABLE_PATTERN.fullmatch(value)
    if full_match:
        name = full_match.group(1)
        if name not in variables:
            raise KeyError(name)
        return variables[name]

    def replace(match: re.Match) -> str:
        name = match.group(1)
        if name not in variables:
            raise KeyError(name)
        return str(variables[name])

    return VARIABLE_PATTERN.sub(replace, value)


def combine_url(base_url: str, endpoint_url: str) -> str:
    if endpoint_url.startswith(("http://", "https://")):
        return endpoint_url
    if not base_url:
        return endpoint_url
    return f"{base_url.rstrip('/')}/{endpoint_url.lstrip('/')}"


def extract_jsonpath(document: Any, expression: str) -> List[Any]:
    if document is None:
        return []
    return [match.value for match in parse_jsonpath(expression).find(document)]


def _compare(actual: Any, operator: str, expected: Any) -> bool:
    if operator in {"eq", "equals"}:
        return actual == expected
    if operator in {"ne", "not_equals"}:
        return actual != expected
    if operator == "contains":
        return expected in actual if actual is not None else False
    if operator == "not_contains":
        return expected not in actual if actual is not None else True
    if operator == "gt":
        return actual > expected
    if operator == "gte":
        return actual >= expected
    if operator == "lt":
        return actual < expected
    if operator == "lte":
        return actual <= expected
    raise ValueError(f"不支持的比较操作：{operator}")


def _result(rule_type: str, passed: bool, expected: Any, actual: Any, message: str, target: str = "") -> Dict[str, Any]:
    return {
        "type": rule_type,
        "target": target,
        "passed": passed,
        "expected": expected,
        "actual": actual,
        "message": message,
    }


def evaluate_assertions(
    rules: Iterable[Dict[str, Any]],
    *,
    status_code: int,
    elapsed_ms: int,
    response_text: str,
    response_json: Any,
    response_headers: Mapping[str, str],
    variables: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    normalized_headers = {key.lower(): value for key, value in response_headers.items()}

    for rule in rules:
        rule_type = str(rule.get("type", "")).strip()
        default_operator = "lte" if rule_type == "response_time" else "eq"
        operator = str(rule.get("operator") or default_operator).strip()
        target = str(rule.get("target") or rule.get("expression") or "").strip()
        expected = rule.get("expected")
        try:
            expected = interpolate(expected, variables)
            if rule_type == "status":
                passed = _compare(status_code, operator, int(expected))
                results.append(_result(rule_type, passed, expected, status_code, f"状态码 {status_code}", target))
            elif rule_type == "body_contains":
                passed = _compare(response_text, operator or "contains", str(expected))
                results.append(_result(rule_type, passed, expected, response_text[:200], "响应正文包含断言", target))
            elif rule_type == "jsonpath":
                matches = extract_jsonpath(response_json, target)
                if operator == "exists":
                    passed = bool(matches)
                    actual = matches[0] if matches else None
                elif operator == "not_exists":
                    passed = not matches
                    actual = matches[0] if matches else None
                else:
                    actual = matches[0] if matches else None
                    passed = bool(matches) and _compare(actual, operator, expected)
                results.append(_result(rule_type, passed, expected, actual, f"JSONPath {target}", target))
            elif rule_type == "header":
                actual = normalized_headers.get(target.lower())
                if operator == "exists":
                    passed = actual is not None
                elif operator == "not_exists":
                    passed = actual is None
                else:
                    passed = actual is not None and _compare(actual, operator, expected)
                results.append(_result(rule_type, passed, expected, actual, f"响应头 {target}", target))
            elif rule_type == "response_time":
                passed = _compare(elapsed_ms, operator or "lte", int(expected))
                results.append(_result(rule_type, passed, expected, elapsed_ms, "响应时间（毫秒）", target))
            elif rule_type == "json_schema":
                schema = rule.get("schema") or expected
                validate(instance=response_json, schema=schema)
                results.append(_result(rule_type, True, "符合 Schema", "符合", "JSON Schema 校验通过", target))
            else:
                results.append(_result(rule_type or "unknown", False, expected, None, "不支持的断言类型", target))
        except (KeyError, TypeError, ValueError, ValidationError, JSONPathError) as exc:
            results.append(_result(rule_type or "unknown", False, expected, None, str(exc), target))
    return results


def apply_extractors(
    extractors: Iterable[Dict[str, Any]],
    response_json: Any,
    variables: Dict[str, Any],
) -> Tuple[List[str], List[Dict[str, Any]]]:
    extracted_names: List[str] = []
    results: List[Dict[str, Any]] = []
    for extractor in extractors:
        name = str(extractor.get("name", "")).strip()
        expression = str(extractor.get("expression", "")).strip()
        try:
            if not name or not expression:
                raise ValueError("变量名和 JSONPath 不能为空")
            matches = extract_jsonpath(response_json, expression)
            if not matches:
                raise ValueError(f"JSONPath 未匹配：{expression}")
            variables[name] = matches[0]
            extracted_names.append(name)
            results.append(_result("extractor", True, expression, f"变量 {name}", f"已提取变量 {name}", name))
        except (TypeError, ValueError, JSONPathError) as exc:
            results.append(_result("extractor", False, expression, None, str(exc), name))
    return extracted_names, results
