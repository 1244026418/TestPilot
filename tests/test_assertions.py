import pytest

from app.services.assertions import (
    apply_extractors,
    combine_url,
    evaluate_assertions,
    extract_jsonpath,
    interpolate,
)


def evaluate(rule, **overrides):
    context = {
        "status_code": 200,
        "elapsed_ms": 120,
        "response_text": '{"user":{"name":"demo"}}',
        "response_json": {"user": {"name": "demo", "roles": ["tester"]}},
        "response_headers": {"Content-Type": "application/json", "X-Request-Id": "abc-123"},
        "variables": {"expected_name": "demo"},
    }
    context.update(overrides)
    return evaluate_assertions([rule], **context)[0]


def test_interpolate_preserves_exact_variable_type():
    assert interpolate("{{count}}", {"count": 3}) == 3


def test_interpolate_nested_request_data():
    source = {"headers": ["Bearer {{token}}"], "user": "{{name}}"}
    assert interpolate(source, {"token": "abc", "name": "demo"}) == {
        "headers": ["Bearer abc"],
        "user": "demo",
    }


def test_interpolate_missing_variable_raises_clear_error():
    with pytest.raises(KeyError, match="token"):
        interpolate("Bearer {{token}}", {})


@pytest.mark.parametrize(
    ("base_url", "endpoint_url", "expected"),
    [
        ("http://localhost:8000/", "/users", "http://localhost:8000/users"),
        ("http://localhost:8000", "users", "http://localhost:8000/users"),
        ("http://localhost:8000", "https://example.com/users", "https://example.com/users"),
        ("", "/users", "/users"),
    ],
)
def test_combine_url(base_url, endpoint_url, expected):
    assert combine_url(base_url, endpoint_url) == expected


def test_extract_jsonpath_supports_nested_arrays():
    assert extract_jsonpath({"users": [{"name": "A"}, {"name": "B"}]}, "$.users[*].name") == ["A", "B"]


def test_status_assertion_passes():
    result = evaluate({"type": "status", "operator": "eq", "expected": 200})
    assert result["passed"] is True
    assert result["actual"] == 200


def test_jsonpath_assertion_uses_environment_variable():
    result = evaluate({"type": "jsonpath", "target": "$.user.name", "operator": "eq", "expected": "{{expected_name}}"})
    assert result["passed"] is True


def test_jsonpath_exists_assertion():
    assert evaluate({"type": "jsonpath", "target": "$.user.roles[0]", "operator": "exists"})["passed"] is True


def test_response_header_assertion_is_case_insensitive():
    assert evaluate({"type": "header", "target": "x-request-id", "operator": "contains", "expected": "abc"})["passed"] is True


def test_response_time_defaults_to_less_than_or_equal():
    assert evaluate({"type": "response_time", "expected": 200})["passed"] is True


def test_body_contains_assertion():
    assert evaluate({"type": "body_contains", "operator": "contains", "expected": "demo"})["passed"] is True


def test_json_schema_assertion_passes():
    rule = {
        "type": "json_schema",
        "schema": {
            "type": "object",
            "required": ["user"],
            "properties": {"user": {"type": "object"}},
        },
    }
    assert evaluate(rule)["passed"] is True


def test_json_schema_assertion_returns_failure_detail():
    rule = {"type": "json_schema", "schema": {"type": "object", "required": ["token"]}}
    result = evaluate(rule)
    assert result["passed"] is False
    assert "required property" in result["message"]


def test_invalid_jsonpath_becomes_failed_assertion():
    result = evaluate({"type": "jsonpath", "target": "$.[", "operator": "exists"})
    assert result["passed"] is False


def test_extractor_writes_runtime_variable_without_returning_secret():
    variables = {}
    names, results = apply_extractors([{"name": "token", "expression": "$.token"}], {"token": "secret-value"}, variables)
    assert names == ["token"]
    assert variables == {"token": "secret-value"}
    assert "secret-value" not in str(results)


def test_extractor_reports_missing_jsonpath():
    names, results = apply_extractors([{"name": "token", "expression": "$.token"}], {}, {})
    assert names == []
    assert results[0]["passed"] is False
