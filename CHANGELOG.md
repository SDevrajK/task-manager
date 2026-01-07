# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-07

### Added
- Initial release: Unified task management tool with CLI and TUI modes
- Interactive TUI built with Textual framework
- Complete CLI with subcommands for task management
- Task list view with color-coded status and priority
- Real-time filtering: All / TODO / IN_PROGRESS / DONE views
- View cycling with Ctrl-H hotkey
- Task detail preview pane
- Task creation and editing screens
- Action dialogs (activate, complete, deactivate, delete)
- CLAUDE.md integration for project workflows
- Activate workflows: quick (status + CLAUDE.md) and PRD-based
- Project management with automatic code/name lookup
- Time tracking and logging
- Advanced search and filtering
- Statistics and time reports
- Natural language date parsing (tomorrow, next Monday, etc.)
- Configuration system with environment variable support
- Comprehensive logging system
- Backward compatible with existing task data format

### Fixed
- **Counter display bug**: Fixed TUI showing 0 for all task counters
- **Status mismatch**: Unified status terminology across CLI and TUI
- **View cycling**: Ctrl-H now works in all views (was only in default view)
- **CLAUDE.md integration**: Properly adds/removes tasks from project documentation

### Changed
- Migrated from separate bash (tasks) and Python (task) scripts to unified tool
- Changed data storage location from `~/.claude/` to `~/projects/task-manager/data/`
- TUI is now default mode when running `task` with no arguments
- Status values: Internal keeps TODO/IN_PROGRESS/DONE/BLOCKED, display uses "Pending/Active/Completed/Blocked"

### Removed
- Old bash script implementation (`~/.local/bin/tasks` - replaced with Python TUI)
- Deprecated natural language interface (task_nlp.py)
- Weekly summary script (tasks-summary) - can be reimplemented as TUI feature if needed

### Technical Details
- Built with Textual 0.30+ for modern TUI experience
- Modern Python packaging with pyproject.toml
- Pip-installable with entry points
- Supports Python 3.8+
- Comprehensive test suite (can be expanded)
- Full type hints for better IDE support

### Migration Notes
**From previous version:**
- Old codebase archived to `~/.claude/scripts/legacy/`
- Data files automatically migrated from `~/.claude/` to `data/` directory
- All existing CLI commands remain functional
- Projects.json and task data formats unchanged

## [Unreleased]

### Planned Features
- Undo support for task modifications
- Custom keyboard binding configuration
- Task templates and quick-create shortcuts
- Recurring/recurring tasks dashboard
- Integration with external calendars
- Colored syntax highlighting in notes
- Mouse support refinements
- Python 3.7 compatibility (currently 3.8+)
- Windows Terminal support improvements
