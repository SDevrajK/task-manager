# Known Issues

## Data Model Issues

### 1. Client Assignment at Task Level (Not Project Level)

**Severity**: Medium
**Status**: Identified (2026-01-09)

**Description**:
Currently, `employer_client` is stored on individual tasks, but logically all tasks in a project belong to the same client(s). This creates a design flaw where:
- Every task in a project must have the same `employer_client` value set manually
- If a project's client changes, every task must be updated individually
- Data is redundant and prone to inconsistency

**Example**:
- Project "eda-calorique" belongs to "HébertLab"
- All 6 tasks in this project had to be manually updated to set `employer_client = "HébertLab"`
- If the project moved to a different lab, all 6 tasks would need updating

**Files Affected**:
- `src/task_manager/models.py` - Task model (has `employer_client` field)
- `src/task_manager/queries.py` - Queries assume client at task level
- `src/task_manager/formatters.py` - Time report grouping relies on task-level client

**Potential Solution**:
1. Move `employer_client` to the Project model (or create a new field `lab` for consistency with your naming)
2. Have tasks inherit the client from their project by default
3. Optionally allow task-level override if a task spans multiple clients (edge case)
4. Update all queries and formatters to use project's client
5. Create migration script to populate project clients from existing task data

**Impact on Features**:
- Time reporting grouping by client works but requires redundant data entry
- Future features (billing, project allocation, etc.) will be easier to implement at project level

**Related Code**:
- Task model: `src/task_manager/models.py:Task`
- Project model: `src/task_manager/models.py:Project`
- Time report query: `src/task_manager/queries.py:get_time_logs_by_date_range()`
- Time report formatter: `src/task_manager/formatters.py:format_time_report()`
