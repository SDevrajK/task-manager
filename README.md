# Task Manager

A unified task management tool with both CLI and interactive TUI (Text User Interface) modes. Manage your tasks efficiently from the command line or navigate through an intuitive terminal interface.

## Features

### Interactive TUI Mode
- **Task List View**: Navigate tasks with arrow keys or Vim bindings (j/k)
- **Color-Coded Status**: Visual distinction between pending, active, and completed tasks
- **Real-Time Filtering**: Cycle through views (All → Pending → Active → Completed)
- **Task Details**: See full task information in a preview pane
- **Keyboard Shortcuts**:
  - `Ctrl-H`: Cycle through filter views
  - `Ctrl-N`: Create new task
  - `↑/↓` or `j/k`: Navigate
  - `Enter`: Select and show actions
  - `q`: Quit

### CLI Mode
Full-featured command-line interface for scripting and automation:
```bash
task add --description "Task name" --project proj-id --deadline tomorrow
task list --status TODO --sort-by deadline
task show 42
task complete 42
task search "keyword"
task stats
```

### Project Integration
- **CLAUDE.md Integration**: Automatically sync tasks with project documentation
- **Activate Workflows**: Quick activation or full PRD-based workflows
- **Project Management**: Track tasks across multiple projects

## Installation

### Option 1: Install from source (Recommended)
```bash
git clone https://github.com/yourusername/task-manager.git
cd task-manager
pip install -e .
```

### Option 2: Manual setup
```bash
# Clone and use directly
git clone https://github.com/yourusername/task-manager.git
cd task-manager

# Create data directory
mkdir -p data

# Run directly
python src/task_manager/cli.py --help
```

## Quick Start

### Launch Interactive TUI
```bash
task
# or
tasks
```

### Use CLI Commands
```bash
# Add a new task
task add --description "Write documentation" --project my-project --deadline 2026-01-15

# List all pending tasks
task list --status TODO

# Show task details
task show 42

# Mark task as complete
task complete 42

# Search tasks
task search "documentation"

# View statistics
task stats
```

## Data Locations

By default, task data is stored in the project directory:
```
~/projects/task-manager/data/
├── task-bucket.json      # All tasks and metadata
├── projects.json         # Project definitions
├── config.json           # Configuration
└── logs/                 # Application logs
```

To use a different data directory, set the environment variable:
```bash
export TASK_MANAGER_DATA="/path/to/data"
task
```

Or specify via CLI:
```bash
task --data-dir /path/to/data list
```

## Configuration

Configuration is stored in `data/config.json`. Customize:
- Color schemes
- Date formats
- Log levels
- Default project
- Time tracking settings

## CLAUDE.md Integration

When a task is activated, it can automatically update your project's `CLAUDE.md`:

### Quick Activation
Updates the task status and adds to `### Upcoming Tasks` section in CLAUDE.md.

### PRD Activation
Updates status and shows recommended next steps:
```
1. Navigate to project directory
2. Run: /create-prd
3. Run: /generate-tasks
4. Run: /process-tasks
```

## CLI Command Reference

### Add Task
```bash
task add [OPTIONS]
  --description TEXT       Task description (required)
  --project PROJECT_ID     Project ID (required)
  --deadline DATE          Due date (e.g., tomorrow, 2026-01-15)
  --priority PRIORITY      high/medium/low (default: medium)
  --task-type TYPE        work/personal/daily (default: work)
  --time-estimate HOURS    Estimated hours
  --employer-client TEXT   Client or employer
  --tags TAG1,TAG2         Comma-separated tags
  --notes TEXT             Additional notes
```

### List Tasks
```bash
task list [OPTIONS]
  --status STATUS          Filter: TODO, IN_PROGRESS, DONE, BLOCKED
  --project ID             Filter by project
  --priority PRIORITY      Filter: high, medium, low
  --deadline-before DATE   Tasks due before date
  --tags TAGS              Filter by tags (match any)
  --all-tags TAGS          Filter by tags (match all)
  --overdue                Show only overdue tasks
  --due-today              Show only tasks due today
  --due-this-week          Show only tasks due this week
  --due-next N             Show tasks due in next N days
  --sort-by FIELD          deadline/priority/status
  --format FORMAT          table/simple/json
```

### Show Task
```bash
task show TASK_ID [--format detailed/json]
```

### Update Task
```bash
task update TASK_ID [OPTIONS]
  --description TEXT       New description
  --status STATUS          New status
  --priority PRIORITY      New priority
  --deadline DATE          New deadline
  --notes TEXT             New notes
```

### Complete Task
```bash
task complete TASK_ID [--notes "Completion notes"]
```

### Delete Task
```bash
task delete TASK_ID --confirm
```

### Log Time
```bash
task log-time TASK_ID --hours HOURS [--date DATE] [--description TEXT]
```

### Search Tasks
```bash
task search QUERY [--search-in field] [--format table/json]
```

### View Statistics
```bash
task stats
```

### Time Reports
```bash
task time-report [OPTIONS]
  --project ID           Filter by project
  --client NAME          Filter by client
  --start-date DATE      Start date
  --end-date DATE        End date
  --group-by project/client
```

### Project Management
```bash
task add-project [OPTIONS]
  --name NAME            Project name (required)
  --code CODE            4-5 char code (required)
  --lab LAB              Lab name
  --path PATH            Project directory path
  --status active/paused/completed
  --description TEXT     Project description
```

## Development

### Setup Development Environment
```bash
pip install -e ".[dev]"
```

### Run Tests
```bash
pytest
```

### Code Quality
```bash
black src/
mypy src/
ruff check src/
```

## Architecture

```
src/task_manager/
├── cli.py                 # CLI entry point
├── models.py              # Data models (Task, Project, etc.)
├── commands.py            # Business logic
├── storage.py             # JSON persistence
├── queries.py             # Task filtering and search
├── formatters.py          # Output formatting
├── validation.py          # Schema validation
├── date_parser.py         # Natural language date parsing
├── logger.py              # Logging infrastructure
├── claude_integration.py  # CLAUDE.md integration
└── tui/                   # Interactive TUI components
    ├── app.py             # Main Textual application
    ├── widgets/           # UI widgets
    └── screens/           # Screen layouts
```

## Keyboard Shortcuts (TUI Mode)

| Shortcut | Action |
|----------|--------|
| `↑` / `↓` | Navigate task list |
| `j` / `k` | Vim-style navigation |
| `Enter` | Show task actions |
| `Ctrl-H` | Cycle filter view |
| `Ctrl-N` | Create new task |
| `Ctrl-F` | Search/filter |
| `/` | Quick search |
| `q` | Quit |

## Troubleshooting

### Tasks not appearing in TUI
- Check that `data/task-bucket.json` exists and is readable
- Verify data format with: `task list --format json`

### CLAUDE.md integration not working
- Ensure project paths are set correctly in `data/projects.json`
- Check that CLAUDE.md has `### Upcoming Tasks` section

### Slow performance with many tasks
- Consider archiving or deleting completed tasks
- Use CLI filters for large queries

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Changelog

See CHANGELOG.md for release notes and version history

## Support

For issues, questions, or suggestions, please open an issue on GitHub:
https://github.com/yourusername/task-manager/issues
