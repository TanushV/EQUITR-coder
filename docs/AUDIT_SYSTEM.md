# Audit Agent and Test Management

This repository includes an audit pipeline that runs automatically after a task group is completed. The audit agent analyzes the relevant code section, generates audit-owned tests, runs them, can unmark tasks or add follow-ups based on results, and produces commentary.

## Overview
- The audit monitor watches the session-local todo plan (created by the orchestrator) and triggers an audit each time a task group transitions to `completed`.
- The audit agent:
  - Builds a focused code summary for the group's section
  - Creates tests under `tests/audit/<group_id>/` (audit-owned)
  - Runs tests and records results in `audits/<task_name>/group_<group_id>/test_report.json`
  - May unmark the group to `in_progress` and add a remediation todo if tests fail
  - Emits a human-readable report at `audits/<task_name>/group_<group_id>/audit.md`
  - Generates detailed model commentary cross-checking requirements and design

## Permissions and Test Ownership
- Audit tests are off-limits to worker agents. Only the audit agent can create/modify them.
- Mutating operations on audit tests require an auth token.
  - Set the token via environment: `EQUITR_AUDIT_TOKEN=your-secret`
  - Or pass `--auth-token your-secret` to the audit monitor CLI.
- Tools that require the token:
  - `audit_create_group_tests`
  - `audit_mark_defective_tests`
  - `audit_remove_defective_tests`

## Running the Audit Monitor
Run as a module:

```bash
python -m equitrcoder.cli.audit_monitor \
  --todo-file docs/<task_name>/todos.json \
  --task-name <task_name> \
  --sections-file docs/<task_name>/group_sections.json \
  --poll-interval 10
```

Environment variable for write operations:

```bash
export EQUITR_AUDIT_TOKEN=your-secret
```

Notes:
- `--sections-file` is optional. See format below. If omitted, the audit scopes to the main package folder `equitrcoder/`.
- The monitor is idempotent and safe to keep running; it will audit only newly completed groups.

## Section Mapping (Optional)
Provide a mapping so the audit only generates tests for the relevant section(s) per group:

```json
{
  "api_layer": ["equitrcoder/api/"],
  "storage": ["equitrcoder/repository/"],
  "default": ["equitrcoder/"]
}
```

Save as `docs/<task_name>/group_sections.json` and pass via `--sections-file`.

## What the Audit Checks
- Codebase summary of the specified section (for context)
- Test generation for that section only
- Test execution results
- If failures are detected, the audit will:
  - Unmark the task group (set status to `in_progress`)
  - Add a todo: `Fix failing audit tests for <group>`
- Commentary cross-checking against `requirements.md` and `design.md`

## Audit Tools (for advanced usage)
- `audit_create_group_tests(group_id, section_paths, auth_token, overwrite=False)`
- `audit_get_group_test_statuses(group_id, pytest_args=[])`
- `audit_list_group_tests(group_id)`
- `audit_mark_defective_tests(group_id, test_patterns_or_paths, auth_token)`
- `audit_remove_defective_tests(group_id, auth_token, remove_files=False)`

These are discoverable tools inside the runtime and can be used by the audit agent. Mutations require a valid `EQUITR_AUDIT_TOKEN`.

## Output Locations
- Audit artifacts: `audits/<task_name>/group_<group_id>/`
  - `summary.txt` — compact code summary of the section
  - `audit.md` — human-readable audit commentary
  - `test_report.json` — structured test run output
- Generated tests: `tests/audit/<group_id>/`
- Defective tests archive: `tests/audit/_defective/<group_id>/`

## Notes
- The generated tests are intentionally conservative and structural. They verify module importability and function presence to gate regressions and drive follow-up work.
- Bulk marking/removing of defective tests is supported for cases where generated tests are determined invalid or out-of-scope.
