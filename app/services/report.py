from html import escape
from pathlib import Path
from typing import List

from app.config import REPORT_DIR
from app.models import TestResult, TestRun


def render_html_report(run: TestRun, results: List[TestResult]) -> str:
    rows = []
    for result in results:
        case = result.case
        rows.append(
            "<tr>"
            f"<td>{escape(case.title)}</td>"
            f"<td>{escape(case.category)}</td>"
            f"<td>{escape(result.status)}</td>"
            f"<td>{'' if result.status_code is None else result.status_code}</td>"
            f"<td>{'' if result.elapsed_ms is None else result.elapsed_ms}</td>"
            f"<td><pre>{escape(result.error or result.response_snippet or '')}</pre></td>"
            "</tr>"
        )

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>TestPilot Run #{run.id}</title>
  <style>
    body {{ font-family: Arial, "Microsoft YaHei", sans-serif; margin: 32px; color: #172033; }}
    h1 {{ margin-bottom: 8px; }}
    .summary {{ display: flex; gap: 12px; margin: 20px 0; }}
    .box {{ border: 1px solid #d7deea; border-radius: 6px; padding: 12px 16px; min-width: 96px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d7deea; padding: 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f4f6f9; }}
    pre {{ white-space: pre-wrap; margin: 0; max-width: 560px; }}
  </style>
</head>
<body>
  <h1>TestPilot 测试报告 #{run.id}</h1>
  <p>项目 ID：{run.project_id}，状态：{escape(run.status)}</p>
  <div class="summary">
    <div class="box"><strong>总数</strong><br>{run.total}</div>
    <div class="box"><strong>通过</strong><br>{run.passed}</div>
    <div class="box"><strong>失败</strong><br>{run.failed}</div>
  </div>
  <table>
    <thead>
      <tr><th>用例</th><th>类型</th><th>结果</th><th>状态码</th><th>耗时 ms</th><th>响应/错误</th></tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body>
</html>
"""
    path = Path(REPORT_DIR) / f"run_{run.id}.html"
    path.write_text(html, encoding="utf-8")
    return str(path)
