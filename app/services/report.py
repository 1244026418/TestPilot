from html import escape
import json
from pathlib import Path
from typing import Any, List

from app.config import REPORT_DIR
from app.models import TestResult, TestRun
from app.utils import from_json_text


CATEGORY_LABELS = {
    "normal": "正常",
    "exception": "异常",
    "boundary": "边界",
    "auth": "鉴权",
}
STATUS_LABELS = {
    "running": "执行中",
    "passed": "通过",
    "failed": "失败",
}


def _display(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _assertion_list(result: TestResult) -> str:
    assertions = from_json_text(result.assertion_results_json, [])
    if not assertions:
        return '<span class="muted">无断言明细</span>'
    items = []
    for assertion in assertions:
        status_class = "passed" if assertion.get("passed") else "failed"
        status_text = "通过" if assertion.get("passed") else "失败"
        message = escape(str(assertion.get("message", "")))
        expected = escape(_display(assertion.get("expected")))
        actual = escape(_display(assertion.get("actual")))
        items.append(
            f'<li><span class="badge {status_class}">{status_text}</span>'
            f"<strong>{message}</strong><small>期望：{expected}；实际：{actual}</small></li>"
        )
    return f'<ul class="assertions">{"".join(items)}</ul>'


def render_html_report(run: TestRun, results: List[TestResult]) -> str:
    rows = []
    for result in results:
        case = result.case
        extracted = from_json_text(result.extracted_variables_json, [])
        rows.append(
            "<tr>"
            f"<td><strong>{escape(case.title)}</strong><small>{escape(result.request_url or '-')}</small></td>"
            f"<td>{escape(CATEGORY_LABELS.get(case.category, case.category))}</td>"
            f'<td><span class="badge {escape(result.status)}">{escape(STATUS_LABELS.get(result.status, result.status))}</span></td>'
            f"<td>{'' if result.status_code is None else result.status_code}</td>"
            f"<td>{'' if result.elapsed_ms is None else result.elapsed_ms}</td>"
            f"<td>{_assertion_list(result)}</td>"
            f"<td>{escape(', '.join(extracted) or '-')}</td>"
            f"<td><pre>{escape(result.error or result.response_snippet or '')}</pre></td>"
            "</tr>"
        )

    environment = escape(run.environment_name or "未指定")
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TestPilot 测试报告 #{run.id}</title>
  <style>
    body {{ font-family: Arial, "Microsoft YaHei", sans-serif; margin: 28px; color: #172033; background: #f4f6f9; }}
    main {{ max-width: 1480px; margin: 0 auto; }}
    h1 {{ margin: 0 0 8px; }}
    p {{ color: #667085; }}
    .summary {{ display: flex; gap: 12px; margin: 20px 0; flex-wrap: wrap; }}
    .box {{ border: 1px solid #d7deea; border-radius: 6px; padding: 12px 16px; min-width: 112px; background: #fff; }}
    table {{ border-collapse: collapse; width: 100%; background: #fff; font-size: 13px; }}
    th, td {{ border: 1px solid #d7deea; padding: 10px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f6; white-space: nowrap; }}
    td small {{ display: block; margin-top: 6px; color: #667085; max-width: 280px; word-break: break-all; }}
    pre {{ white-space: pre-wrap; margin: 0; max-width: 360px; max-height: 180px; overflow: auto; }}
    .badge {{ display: inline-block; border-radius: 4px; padding: 2px 6px; font-size: 12px; font-weight: 700; }}
    .badge.passed {{ color: #087443; background: #e8f7ef; }}
    .badge.failed {{ color: #b42318; background: #feeceb; }}
    .assertions {{ min-width: 280px; margin: 0; padding: 0; list-style: none; }}
    .assertions li {{ padding: 5px 0; border-bottom: 1px solid #edf0f5; }}
    .assertions li:last-child {{ border-bottom: 0; }}
    .assertions strong {{ margin-left: 6px; }}
    .muted {{ color: #98a2b3; }}
  </style>
</head>
<body>
<main>
  <h1>TestPilot 测试报告 #{run.id}</h1>
  <p>项目 ID：{run.project_id}；测试环境：{environment}；状态：{escape(STATUS_LABELS.get(run.status, run.status))}</p>
  <div class="summary">
    <div class="box"><strong>总数</strong><br>{run.total}</div>
    <div class="box"><strong>通过</strong><br>{run.passed}</div>
    <div class="box"><strong>失败</strong><br>{run.failed}</div>
  </div>
  <table>
    <thead>
      <tr><th>用例与请求</th><th>类型</th><th>结果</th><th>状态码</th><th>耗时 ms</th><th>断言明细</th><th>提取变量</th><th>响应/错误</th></tr>
    </thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</main>
</body>
</html>
"""
    path = Path(REPORT_DIR) / f"run_{run.id}.html"
    path.write_text(html, encoding="utf-8")
    return str(path)
