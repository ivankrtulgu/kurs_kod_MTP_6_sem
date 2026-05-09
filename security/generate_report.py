"""
Security Report Generator
Генератор сводного отчета по безопасности
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class SecurityReportGenerator:
    """Генератор HTML-отчета по результатам сканирования безопасности"""

    def __init__(self, reports_dir: str = "security/reports"):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def load_json_report(self, filename: str) -> Dict[str, Any]:
        """Загрузка JSON-отчета"""
        filepath = self.reports_dir / filename
        if not filepath.exists():
            return {}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def parse_bandit_report(self) -> Dict[str, Any]:
        """Парсинг отчета Bandit"""
        report = self.load_json_report("bandit_report.json")
        if not report:
            return {"total": 0, "by_severity": {}}

        results = report.get("results", [])
        by_severity = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for issue in results:
            severity = issue.get("issue_severity", "LOW")
            by_severity[severity] = by_severity.get(severity, 0) + 1

        return {
            "total": len(results),
            "by_severity": by_severity,
            "issues": results[:10]  # Топ-10 проблем
        }

    def parse_safety_report(self) -> Dict[str, Any]:
        """Парсинг отчета Safety"""
        report = self.load_json_report("safety_report.json")
        if not report:
            return {"total": 0, "vulnerabilities": []}

        vulnerabilities = report.get("vulnerabilities", [])

        return {
            "total": len(vulnerabilities),
            "vulnerabilities": vulnerabilities[:10]
        }

    def parse_pip_audit_report(self) -> Dict[str, Any]:
        """Парсинг отчета pip-audit"""
        report = self.load_json_report("pip_audit_report.json")
        if not report:
            return {"total": 0, "vulnerabilities": []}

        vulnerabilities = report.get("vulnerabilities", [])

        return {
            "total": len(vulnerabilities),
            "vulnerabilities": vulnerabilities[:10]
        }

    def parse_secrets_report(self) -> Dict[str, Any]:
        """Парсинг отчета detect-secrets"""
        report = self.load_json_report("secrets_baseline.json")
        if not report:
            return {"total": 0, "files": 0, "secrets": []}

        results = report.get("results", {})
        total_secrets = sum(len(secrets) for secrets in results.values())

        return {
            "total": total_secrets,
            "files": len(results)
        }

    def parse_pylint_report(self) -> Dict[str, Any]:
        """Парсинг отчета Pylint"""
        report = self.load_json_report("pylint_report.json")
        if not report:
            return {"total": 0, "by_type": {}}

        by_type = {}
        for issue in report:
            msg_type = issue.get("type", "unknown")
            by_type[msg_type] = by_type.get(msg_type, 0) + 1

        return {
            "total": len(report),
            "by_type": by_type,
            "issues": report[:10]
        }

    def parse_semgrep_report(self) -> Dict[str, Any]:
        """Парсинг отчета Semgrep"""
        report = self.load_json_report("semgrep_report.json")
        if not report:
            return {"total": 0, "by_severity": {}}

        results = report.get("results", [])
        by_severity = {"ERROR": 0, "WARNING": 0, "INFO": 0}

        for issue in results:
            severity = issue.get("extra", {}).get("severity", "INFO")
            by_severity[severity] = by_severity.get(severity, 0) + 1

        return {
            "total": len(results),
            "by_severity": by_severity,
            "issues": results[:10]
        }

    def generate_html_report(self) -> str:
        """Генерация HTML-отчета"""
        bandit = self.parse_bandit_report()
        safety = self.parse_safety_report()
        pip_audit = self.parse_pip_audit_report()
        secrets = self.parse_secrets_report()
        pylint = self.parse_pylint_report()
        semgrep = self.parse_semgrep_report()

        total_issues = (
            bandit["total"] +
            safety["total"] +
            pip_audit["total"] +
            secrets["total"] +
            pylint["total"] +
            semgrep["total"]
        )

        critical_issues = (
            bandit["by_severity"].get("HIGH", 0) +
            safety["total"] +
            semgrep["by_severity"].get("ERROR", 0)
        )

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Scan Report - Library Management System</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}

        .subtitle {{
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .summary-card.critical {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}

        .summary-card.warning {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }}

        .summary-card h3 {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .summary-card .number {{
            font-size: 3em;
            font-weight: bold;
            line-height: 1;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }}

        .tool-report {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }}

        .tool-report h3 {{
            color: #2c3e50;
            margin-bottom: 15px;
        }}

        .stats {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }}

        .stat {{
            background: white;
            padding: 10px 20px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}

        .stat-label {{
            font-size: 0.85em;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
        }}

        .severity-high {{
            color: #e74c3c;
        }}

        .severity-medium {{
            color: #f39c12;
        }}

        .severity-low {{
            color: #3498db;
        }}

        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}

        .timestamp {{
            color: #95a5a6;
            font-size: 0.9em;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}

        th {{
            background: #34495e;
            color: white;
            font-weight: 600;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Security Scan Report</h1>
        <p class="subtitle">Library Management System</p>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <div class="summary-card critical">
                <h3>Critical Issues</h3>
                <div class="number">{critical_issues}</div>
            </div>
            <div class="summary-card warning">
                <h3>Total Issues</h3>
                <div class="number">{total_issues}</div>
            </div>
            <div class="summary-card">
                <h3>Scans Completed</h3>
                <div class="number">6</div>
            </div>
        </div>

        <div class="section">
            <h2>SAST Analysis</h2>

            <div class="tool-report">
                <h3>Bandit - Python Security Scanner</h3>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-label">Total Issues</div>
                        <div class="stat-value">{bandit["total"]}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">High Severity</div>
                        <div class="stat-value severity-high">{bandit["by_severity"].get("HIGH", 0)}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Medium Severity</div>
                        <div class="stat-value severity-medium">{bandit["by_severity"].get("MEDIUM", 0)}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Low Severity</div>
                        <div class="stat-value severity-low">{bandit["by_severity"].get("LOW", 0)}</div>
                    </div>
                </div>
            </div>

            <div class="tool-report">
                <h3>Semgrep - Advanced SAST</h3>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-label">Total Findings</div>
                        <div class="stat-value">{semgrep["total"]}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Errors</div>
                        <div class="stat-value severity-high">{semgrep["by_severity"].get("ERROR", 0)}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Warnings</div>
                        <div class="stat-value severity-medium">{semgrep["by_severity"].get("WARNING", 0)}</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Dependency Security</h2>

            <div class="tool-report">
                <h3>Safety - Known Vulnerabilities (CVE)</h3>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-label">Vulnerabilities Found</div>
                        <div class="stat-value severity-high">{safety["total"]}</div>
                    </div>
                </div>
            </div>

            <div class="tool-report">
                <h3>pip-audit - Package Audit</h3>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-label">Vulnerabilities Found</div>
                        <div class="stat-value severity-high">{pip_audit["total"]}</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Code Quality</h2>

            <div class="tool-report">
                <h3>Pylint - Static Code Analysis</h3>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-label">Total Issues</div>
                        <div class="stat-value">{pylint["total"]}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Errors</div>
                        <div class="stat-value severity-high">{pylint["by_type"].get("error", 0)}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Warnings</div>
                        <div class="stat-value severity-medium">{pylint["by_type"].get("warning", 0)}</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Secrets Detection</h2>

            <div class="tool-report">
                <h3>detect-secrets - Secret Scanner</h3>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-label">Potential Secrets</div>
                        <div class="stat-value severity-high">{secrets["total"]}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Files Scanned</div>
                        <div class="stat-value">{secrets["files"]}</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Security scan completed. Review individual reports for detailed findings.</p>
            <p>Reports location: security/reports/</p>
        </div>
    </div>
</body>
</html>
"""

        output_path = self.reports_dir / "security_summary.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return str(output_path)


def main():
    """Главная функция"""
    generator = SecurityReportGenerator()
    report_path = generator.generate_html_report()
    print(f"Security summary report generated: {report_path}")


if __name__ == "__main__":
    main()
