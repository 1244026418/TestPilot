from datetime import datetime
import time
from typing import Any, Dict, List, Optional

import requests
from sqlalchemy.orm import Session, selectinload

from app.models import ApiEndpoint, Project, TestEnvironment, TestResult, TestRun
from app.services.assertions import apply_extractors, combine_url, evaluate_assertions, interpolate
from app.services.report import render_html_report
from app.utils import from_json_text, to_json_text


def _legacy_assertions(case, endpoint) -> List[Dict[str, Any]]:
    rules = list(from_json_text(case.assertions_json, []))
    if not any(rule.get("type") == "status" for rule in rules):
        expected_status = case.expected_status or endpoint.expected_status
        rules.insert(0, {"type": "status", "operator": "eq", "expected": expected_status})
    if case.expected_contains and not any(rule.get("type") == "body_contains" for rule in rules):
        rules.append({"type": "body_contains", "operator": "contains", "expected": case.expected_contains})
    return rules


def _select_environment(db: Session, project_id: int, environment_id: Optional[int]) -> Optional[TestEnvironment]:
    query = db.query(TestEnvironment).filter(TestEnvironment.project_id == project_id)
    if environment_id is not None:
        environment = query.filter(TestEnvironment.id == environment_id).first()
        if environment is None:
            raise ValueError("测试环境不存在")
        return environment
    return query.filter(TestEnvironment.is_active.is_(True)).first()


def execute_project(db: Session, project_id: int, environment_id: Optional[int] = None) -> TestRun:
    project = (
        db.query(Project)
        .options(selectinload(Project.endpoints).selectinload(ApiEndpoint.cases))
        .filter(Project.id == project_id)
        .first()
    )
    if project is None:
        raise ValueError("项目不存在")

    environment = _select_environment(db, project_id, environment_id)
    variables: Dict[str, Any] = from_json_text(environment.variables_json) if environment else {}
    base_url = environment.base_url if environment else ""
    run = TestRun(
        project_id=project_id,
        environment_id=environment.id if environment else None,
        environment_name=environment.name if environment else None,
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    results: List[TestResult] = []
    extracted_names: List[str] = []
    for endpoint in sorted(project.endpoints, key=lambda item: item.id):
        endpoint_headers = from_json_text(endpoint.headers_json)
        endpoint_body = from_json_text(endpoint.body_json)
        for case in sorted(endpoint.cases, key=lambda item: item.id):
            started = time.perf_counter()
            status_code = None
            elapsed_ms = None
            error = None
            snippet = None
            request_url = None
            assertion_results: List[Dict[str, Any]] = []
            case_extracted_names: List[str] = []

            try:
                case_headers = from_json_text(case.request_headers_json)
                case_body = from_json_text(case.request_body_json)
                headers = interpolate({**endpoint_headers, **case_headers}, variables)
                body = interpolate(case_body if case_body else endpoint_body, variables)
                request_url = interpolate(combine_url(base_url, endpoint.url), variables)
                response = requests.request(
                    method=endpoint.method.upper(),
                    url=request_url,
                    headers=headers,
                    json=body if body else None,
                    timeout=8,
                )
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                status_code = response.status_code
                snippet = response.text[:800]
                try:
                    response_json = response.json()
                except ValueError:
                    response_json = None

                assertion_results = evaluate_assertions(
                    _legacy_assertions(case, endpoint),
                    status_code=status_code,
                    elapsed_ms=elapsed_ms,
                    response_text=response.text,
                    response_json=response_json,
                    response_headers=response.headers,
                    variables=variables,
                )
                case_extracted_names, extractor_results = apply_extractors(
                    from_json_text(case.extractors_json, []),
                    response_json,
                    variables,
                )
                assertion_results.extend(extractor_results)
                extracted_names.extend(name for name in case_extracted_names if name not in extracted_names)
                for name in case_extracted_names:
                    extracted_value = variables.get(name)
                    if snippet and isinstance(extracted_value, (str, int, float, bool)):
                        snippet = snippet.replace(str(extracted_value), "***")
            except KeyError as exc:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                error = f"变量未定义：{exc.args[0]}"
            except requests.RequestException as exc:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                error = str(exc)
            except (TypeError, ValueError) as exc:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                error = str(exc)

            passed = error is None and bool(assertion_results) and all(item["passed"] for item in assertion_results)
            result = TestResult(
                run_id=run.id,
                testcase_id=case.id,
                status="passed" if passed else "failed",
                status_code=status_code,
                elapsed_ms=elapsed_ms,
                request_url=request_url,
                error=error,
                response_snippet=snippet,
                assertion_results_json=to_json_text(assertion_results),
                extracted_variables_json=to_json_text(case_extracted_names),
            )
            db.add(result)
            results.append(result)

    run.total = len(results)
    run.passed = sum(1 for result in results if result.status == "passed")
    run.failed = run.total - run.passed
    run.status = "passed" if run.total > 0 and run.failed == 0 else "failed"
    run.finished_at = datetime.utcnow()
    run.summary_json = to_json_text(
        {
            "passed": run.passed,
            "failed": run.failed,
            "total": run.total,
            "environment": run.environment_name,
            "extracted_variables": extracted_names,
        }
    )
    db.commit()

    for result in results:
        db.refresh(result)
    db.refresh(run)
    run.report_path = render_html_report(run, results)
    db.commit()
    db.refresh(run)
    return run
