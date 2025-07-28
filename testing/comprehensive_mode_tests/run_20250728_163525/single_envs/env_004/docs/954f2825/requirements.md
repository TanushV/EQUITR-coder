# requirements.md

## 1. Project Overview
Create an automated static-analysis audit tool that inspects the file `test_code.py`, identifies potential code-quality issues, and produces a human-readable report.

## 2. Functional Requirements
| ID | Requirement | Priority |
|---|---|---|
| FR-1 | **File Access** – The tool must open and read `test_code.py` from the current working directory. | Must |
| FR-2 | **Static Analysis** – Detect the following categories of issues:<br>- Syntax errors<br>- Undefined variables / imports<br>- Unused variables or imports<br>- Code-style violations (PEP 8)<br>- Security anti-patterns (e.g., `eval`, hard-coded secrets)<br>- Complexity hotspots (cyclomatic complexity > 10)<br>- Missing docstrings for public functions/classes | Must |
| FR-3 | **Severity Levels** – Classify each finding as `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW`. | Must |
| FR-4 | **Report Generation** – Emit a markdown report named `audit_report.md` that includes:<br>- Executive summary (count of issues by severity)<br>- Detailed list of findings with line numbers, issue type, description, and suggested fix | Must |
| FR-5 | **Console Output** – Print a short summary to stdout (total issues and highest severity). | Should |
| FR-6 | **Exit Codes** – Return exit code `0` if no critical issues, `1` otherwise, enabling CI integration. | Should |

## 3. Technical Requirements
| ID | Requirement | Details |
|---|---|---|
| TR-1 | **Language** – Implement in Python 3.9+. | |
| TR-2 | **Core Libraries** – Use only the Python standard library plus:<br>- `ast` for parsing<br>- `flake8` or `pylint` for style/complexity checks (via subprocess if needed) | |
| TR-3 | **Performance** – Complete audit of a 1,000-line file in < 2 seconds on a modern laptop. | |
| TR-4 | **Portability** – Run on Windows, macOS, and Linux without additional installation. | |
| TR-5 | **Configuration** – Optional `audit_config.json` to enable/disable specific checks. | Nice-to-have |
| TR-6 | **Logging** – Emit debug logs to `audit.log` when `--debug` flag is provided. | Nice-to-have |

## 4. Success Criteria
- [ ] `audit_report.md` is created and contains at least one finding if issues exist.
- [ ] Running the tool on a clean PEP 8-compliant file yields zero findings and exit code 0.
- [ ] Running the tool on a file with deliberate critical issues yields exit code 1 and lists them in the report.
- [ ] The markdown report renders correctly in GitHub’s viewer.
- [ ] A CI pipeline step using the tool fails the build when critical issues are introduced.