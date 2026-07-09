from datetime import datetime
import time
from typing import List

import requests
from sqlalchemy.orm import Session, selectinload

from app.models import Project, TestResult, TestRun
from app.services.report import render_html_report
from app.utils import from_json_text, to_json_text


def execute_project(db: Session, project_id: int) -> TestRun:
    project = (
        db.query(Project)
        .options(selectinload(Project.endpoints).selectinload("*"))
        .filter(Project.id == project_id)
        .first()
    )
    if project is None:
        raise ValueError("project not found")

    run = TestRun(project_id=project_id, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    results: List[TestResult] = []
    for endpoint in project.endpoints:
        endpoint_headers = from_json_text(endpoint.headers_json)
        endpoint_body = from_json_text(endpoint.body_json)
        for case in endpoint.cases:
            case_headers = from_json_text(case.request_headers_json)
            case_body = from_json_text(case.request_body_json)
            headers = {**endpoint_headers, **case_headers}
            body = case_body if case_body else endpoint_body
            expected_status = case.expected_status or endpoint.expected_status
            started = time.perf_counter()
            status_code = None
            error = None
            snippet = None
            passed = False

            try:
                response = requests.request(
                    method=endpoint.method.upper(),
                    url=endpoint.url,
                    headers=headers,
                    json=body if body else None,
                    timeout=8,
                )
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                status_code = response.status_code
                snippet = response.text[:800]
                contains_ok = True
                if case.expected_contains:
                    contains_ok = case.expected_contains in response.text
                passed = response.status_code == expected_status and contains_ok
            except requests.RequestException as exc:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                error = str(exc)

            result = TestResult(
                run_id=run.id,
                testcase_id=case.id,
                status="passed" if passed else "failed",
                status_code=status_code,
                elapsed_ms=elapsed_ms,
                error=error,
                response_snippet=snippet,
            )
            db.add(result)
            results.append(result)

    run.total = len(results)
    run.passed = sum(1 for result in results if result.status == "passed")
    run.failed = run.total - run.passed
    run.status = "passed" if run.failed == 0 else "failed"
    run.finished_at = datetime.utcnow()
    run.summary_json = to_json_text({"passed": run.passed, "failed": run.failed, "total": run.total})
    db.commit()

    for result in results:
        db.refresh(result)
    db.refresh(run)
    run.report_path = render_html_report(run, results)
    db.commit()
    db.refresh(run)
    return run
