import argparse
import html
import json
from pathlib import Path
from typing import Dict, List, Tuple


def load_report(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def to_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_health(value: str) -> str:
    text = (value or "").strip().lower()
    if text in {"warning", "warn", "предупреждение"}:
        return "warning"
    if text in {"critical", "bad", "unhealthy", "ошибка"}:
        return "critical"
    return "ok"


def analyze(data: Dict) -> Dict:
    issues = []
    score = 100

    summary = data.get("summary") or {}

    problem_devices = to_int(summary.get("problemDevices"))
    windows_event_errors = to_int(summary.get("windowsEventErrors"))
    integrity_issues = bool(summary.get("systemIntegrityIssues"))
    service_issues = to_int(summary.get("criticalServicesIssues"))
    defender_issues = to_int(summary.get("defenderIssues"))
    temp_warnings = to_int(summary.get("temperatureWarnings"))

    if problem_devices > 0:
        issues.append(("warning", f"Проблемные устройства: {problem_devices}"))
        score -= 20

    if windows_event_errors > 10:
        issues.append(("warning", f"Много ошибок Windows Event Log: {windows_event_errors}"))
        score -= 15

    if integrity_issues:
        issues.append(("critical", "Обнаружены проблемы с целостностью системы"))
        score -= 30

    if service_issues > 0:
        issues.append(("warning", f"Есть проблемы критических служб: {service_issues}"))
        score -= 15

    if defender_issues > 0:
        issues.append(("warning", f"Defender сообщает о проблемах: {defender_issues}"))
        score -= 12

    if temp_warnings > 0:
        issues.append(("warning", f"Температурные предупреждения: {temp_warnings}"))
        score -= 10

    for disk in data.get("disks", []) or []:
        disk_name = str(disk.get("disk") or disk.get("name") or "Неизвестный диск")
        health = normalize_health(str(disk.get("health") or ""))
        if health in {"warning", "critical"}:
            level = "critical" if health == "critical" else "warning"
            issues.append((level, f"Проблема с диском: {disk_name}"))
            score -= 25 if level == "critical" else 15

    score = max(score, 0)
    if score >= 80:
        overall = "Хорошо"
    elif score >= 50:
        overall = "Есть проблемы"
    else:
        overall = "Критично"

    return {
        "overall": overall,
        "score": score,
        "issues": issues,
    }


def issue_class(level: str) -> str:
    if level == "critical":
        return "bad"
    if level == "warning":
        return "warn"
    return "good"


def render_issues(issues: List[Tuple[str, str]]) -> str:
    if not issues:
        return "<li class=\"good\">Проблем не обнаружено</li>"

    return "\n".join(
        f"<li class=\"{issue_class(level)}\"><b>{html.escape(level.upper())}</b>: {html.escape(text)}</li>"
        for level, text in issues
    )


def render_disks(disks: List[Dict]) -> str:
    if not disks:
        return "<tr><td colspan=\"4\">Нет данных по дискам</td></tr>"

    rows = []
    for disk in disks:
        disk_name = html.escape(str(disk.get("disk") or "n/a"))
        media = html.escape(str(disk.get("mediaType") or "n/a"))
        health = html.escape(str(disk.get("health") or "n/a"))
        size = html.escape(str(disk.get("size") or "n/a"))
        rows.append(f"<tr><td>{disk_name}</td><td>{media}</td><td>{health}</td><td>{size}</td></tr>")
    return "\n".join(rows)


def build_html(data: Dict, analysis: Dict) -> str:
    summary = data.get("summary") or {}
    computer_name = html.escape(str(data.get("computerName") or "Неизвестно"))
    os_version = html.escape(str(data.get("osVersion") or "Неизвестно"))
    run_mode = html.escape(str(data.get("runMode") or "Неизвестно"))
    run_status = html.escape(str(data.get("runStatus") or "Неизвестно"))

    score = int(analysis.get("score", 0))
    overall = html.escape(str(analysis.get("overall", "Неизвестно")))
    overall_class = "good" if score >= 80 else "warn" if score >= 50 else "bad"

    problem_devices = to_int(summary.get("problemDevices"))
    windows_event_errors = to_int(summary.get("windowsEventErrors"))
    defender_issues = to_int(summary.get("defenderIssues"))

    issues_html = render_issues(analysis.get("issues", []))
    disks_html = render_disks(data.get("disks", []) or [])

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Ultra Windows Diagnostic Report</title>
  <style>
    :root {{
      --bg-a: #eef7f3;
      --bg-b: #dfeff0;
      --card: #ffffff;
      --line: #d8e6df;
      --text: #1d2a2a;
      --muted: #4f6262;
      --good: #1f7a44;
      --warn: #a86b00;
      --bad: #b73a3a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--text);
      font-family: "Trebuchet MS", "Segoe UI", sans-serif;
      background: radial-gradient(circle at 10% 10%, #f8fffd 0%, transparent 50%),
                  linear-gradient(150deg, var(--bg-a), var(--bg-b));
    }}
    .container {{ max-width: 980px; margin: 24px auto; padding: 0 14px; }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px;
      margin-bottom: 14px;
      box-shadow: 0 8px 20px rgba(28, 60, 50, 0.08);
    }}
    h1, h2 {{ margin: 0 0 10px 0; }}
    h1 {{ font-size: 28px; letter-spacing: 0.2px; }}
    h2 {{ font-size: 20px; }}
    p {{ margin: 8px 0; }}
    .meta {{ color: var(--muted); font-size: 13px; }}
    .kpi-grid {{
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      margin-top: 10px;
    }}
    .kpi {{
      border: 1px dashed var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #fbfefe;
    }}
    .kpi .label {{ color: var(--muted); font-size: 12px; }}
    .kpi .value {{ font-size: 20px; font-weight: 700; margin-top: 2px; }}
    ul {{ margin: 8px 0 0 0; padding-left: 20px; }}
    li {{ margin-bottom: 6px; }}
    .good {{ color: var(--good); }}
    .warn {{ color: var(--warn); }}
    .bad {{ color: var(--bad); }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid var(--line); font-size: 14px; }}
    th {{ color: var(--muted); font-weight: 600; }}
    @media (max-width: 640px) {{
      h1 {{ font-size: 24px; }}
      .kpi .value {{ font-size: 18px; }}
      th, td {{ font-size: 13px; padding: 7px; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <section class="card">
      <h1>Отчет диагностики Windows</h1>
      <p><b>Компьютер:</b> {computer_name}</p>
      <p><b>ОС:</b> {os_version}</p>
      <p><b>Режим:</b> {run_mode}</p>
      <p><b>Статус выполнения:</b> {run_status}</p>
      <p><b>Итог:</b> <span class="{overall_class}">{overall}</span></p>
      <p><b>Оценка:</b> <span class="{overall_class}">{score}/100</span></p>
      <div class="kpi-grid">
        <div class="kpi"><div class="label">Проблемные устройства</div><div class="value">{problem_devices}</div></div>
        <div class="kpi"><div class="label">Ошибки событий Windows</div><div class="value">{windows_event_errors}</div></div>
        <div class="kpi"><div class="label">Проблемы Defender</div><div class="value">{defender_issues}</div></div>
      </div>
    </section>

    <section class="card">
      <h2>Найденные проблемы</h2>
      <ul>
        {issues_html}
      </ul>
    </section>

    <section class="card">
      <h2>Состояние дисков</h2>
      <table>
        <thead>
          <tr><th>Диск</th><th>Тип</th><th>Здоровье</th><th>Размер</th></tr>
        </thead>
        <tbody>
          {disks_html}
        </tbody>
      </table>
    </section>

    <section class="card meta">
      Сгенерировано автоматически скриптом analyze_report.py
    </section>
  </div>
</body>
</html>
"""


def save_html(content: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze diagnostic JSON and generate HTML report")
    parser.add_argument("input_json", nargs="?", default="report.json")
    parser.add_argument("output_html", nargs="?", default="report.html")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_json)
    output_path = Path(args.output_html)

    if not input_path.exists():
        print(f"ERROR: input JSON not found: {input_path}")
        return 1

    data = load_report(input_path)
    analysis = analyze(data)
    html_content = build_html(data, analysis)
    save_html(html_content, output_path)

    print(f"HTML-отчет сохранен: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
