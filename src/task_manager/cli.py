#!/usr/bin/env python3
"""Task management CLI - Standalone tool for managing tasks without AI dependency."""

import argparse
import sys
from pathlib import Path

# Add task_manager to path
sys.path.insert(0, str(Path(__file__).parent))

from task_manager.config import Config
from task_manager.logger import TaskLogger
from task_manager.commands import TaskCommands


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for task CLI."""
    parser = argparse.ArgumentParser(
        description="Task management system - manage tasks without AI dependency",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  task add --description "Write report" --project project-a --deadline tomorrow
  task list --status TODO --sort-by deadline
  task show 42
  task update 42 --status IN_PROGRESS
  task complete 42
  task log-time 42 --hours 2.5 --description "fixed bug"
  task search "api"
  task stats
  task                          # Launch interactive TUI
        """,
    )

    # Global options
    parser.add_argument(
        "--version",
        action="version",
        version="task-manager 1.0.0",
    )
    parser.add_argument(
        "--data-dir",
        help="Path to data directory (default: ~/projects/task-manager/data)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # ADD command
    add_parser = subparsers.add_parser("add", help="Add new task")
    add_parser.add_argument(
        "--description", "-d",
        required=True,
        help="Task description",
    )
    add_parser.add_argument(
        "--project", "-p",
        required=True,
        help="Project ID",
    )
    add_parser.add_argument(
        "--task-type", "-t",
        default="work",
        choices=["work", "personal", "daily"],
        help="Task type (default: work)",
    )
    add_parser.add_argument(
        "--priority",
        default="medium",
        choices=["high", "medium", "low"],
        help="Priority level (default: medium)",
    )
    add_parser.add_argument(
        "--deadline",
        help="Deadline (YYYY-MM-DD or natural language like 'tomorrow')",
    )
    add_parser.add_argument(
        "--time-estimate",
        type=float,
        help="Time estimate in hours",
    )
    add_parser.add_argument(
        "--employer-client",
        help="Employer or client name",
    )
    add_parser.add_argument(
        "--tags",
        help="Comma-separated tags",
    )
    add_parser.add_argument(
        "--notes",
        help="Additional notes",
    )

    # LIST command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument(
        "--status",
        choices=["TODO", "IN_PROGRESS", "DONE", "BLOCKED"],
        help="Filter by status",
    )
    list_parser.add_argument(
        "--project", "-p",
        help="Filter by project",
    )
    list_parser.add_argument(
        "--task-type", "-t",
        help="Filter by task type",
    )
    list_parser.add_argument(
        "--priority",
        help="Filter by priority",
    )
    list_parser.add_argument(
        "--deadline-before",
        help="Tasks due before date (YYYY-MM-DD)",
    )
    list_parser.add_argument(
        "--tags",
        help="Filter by tags (comma-separated, match any)",
    )
    list_parser.add_argument(
        "--all-tags",
        help="Filter by tags (comma-separated, match all)",
    )
    list_parser.add_argument(
        "--overdue",
        action="store_true",
        help="Show only overdue tasks",
    )
    list_parser.add_argument(
        "--due-today",
        action="store_true",
        help="Show only tasks due today",
    )
    list_parser.add_argument(
        "--due-this-week",
        action="store_true",
        help="Show only tasks due this week",
    )
    list_parser.add_argument(
        "--due-next",
        type=int,
        metavar="N",
        help="Show tasks due in next N days",
    )
    list_parser.add_argument(
        "--sort-by",
        default="deadline",
        choices=["deadline", "priority", "status"],
        help="Sort order (default: deadline)",
    )
    list_parser.add_argument(
        "--format",
        default="table",
        choices=["table", "simple", "json"],
        help="Output format (default: table)",
    )

    # SHOW command
    show_parser = subparsers.add_parser("show", help="Show task details")
    show_parser.add_argument(
        "task_id",
        type=int,
        help="Task ID",
    )
    show_parser.add_argument(
        "--format",
        default="detailed",
        choices=["detailed", "json"],
        help="Output format (default: detailed)",
    )

    # UPDATE command
    update_parser = subparsers.add_parser("update", help="Update task")
    update_parser.add_argument(
        "task_id",
        type=int,
        help="Task ID",
    )
    update_parser.add_argument(
        "--description",
        help="New description",
    )
    update_parser.add_argument(
        "--status",
        help="New status",
    )
    update_parser.add_argument(
        "--priority",
        help="New priority",
    )
    update_parser.add_argument(
        "--deadline",
        help="New deadline",
    )
    update_parser.add_argument(
        "--notes",
        help="New notes",
    )
    update_parser.add_argument(
        "--task-type",
        help="New task type",
    )
    update_parser.add_argument(
        "--employer-client",
        help="New employer/client",
    )
    update_parser.add_argument(
        "--time-estimate",
        type=float,
        help="New time estimate",
    )
    update_parser.add_argument(
        "--tags",
        help="New tags (comma-separated)",
    )

    # COMPLETE command
    complete_parser = subparsers.add_parser("complete", help="Mark task as complete")
    complete_parser.add_argument(
        "task_id",
        type=int,
        help="Task ID",
    )
    complete_parser.add_argument(
        "--notes",
        help="Completion notes",
    )

    # DELETE command
    delete_parser = subparsers.add_parser("delete", help="Delete task")
    delete_parser.add_argument(
        "task_id",
        type=int,
        help="Task ID",
    )
    delete_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm deletion",
    )

    # LOG-TIME command
    logtime_parser = subparsers.add_parser("log-time", help="Log time spent")
    logtime_parser.add_argument(
        "task_id",
        type=int,
        help="Task ID",
    )
    logtime_parser.add_argument(
        "--hours",
        type=float,
        required=True,
        help="Hours spent",
    )
    logtime_parser.add_argument(
        "--description",
        default="",
        help="What was done",
    )
    logtime_parser.add_argument(
        "--date",
        help="Date (YYYY-MM-DD, default: today)",
    )

    # SEARCH command
    search_parser = subparsers.add_parser("search", help="Search tasks")
    search_parser.add_argument(
        "query",
        help="Search query",
    )
    search_parser.add_argument(
        "--search-in",
        choices=["description", "notes", "tags", "client"],
        help="Search in specific field (default: all)",
    )
    search_parser.add_argument(
        "--format",
        default="table",
        choices=["table", "json"],
        help="Output format (default: table)",
    )

    # STATS command
    subparsers.add_parser("stats", help="Show task statistics")

    # TIME-REPORT command
    report_parser = subparsers.add_parser("time-report", help="Generate time report")
    report_parser.add_argument(
        "--project",
        help="Filter by project",
    )
    report_parser.add_argument(
        "--client",
        help="Filter by client",
    )
    report_parser.add_argument(
        "--start-date",
        help="Start date (YYYY-MM-DD)",
    )
    report_parser.add_argument(
        "--end-date",
        help="End date (YYYY-MM-DD)",
    )
    report_parser.add_argument(
        "--group-by",
        default="project",
        choices=["project", "client"],
        help="Group report by (default: project)",
    )

    # ADD-PROJECT command
    addproject_parser = subparsers.add_parser("add-project", help="Add new project")
    addproject_parser.add_argument(
        "--id",
        required=False,
        help="Project ID (e.g., my-project). If not provided, auto-generated from project name.",
    )
    addproject_parser.add_argument(
        "--name",
        required=True,
        help="Full project name",
    )
    addproject_parser.add_argument(
        "--code",
        required=True,
        help="Project code (4-5 characters, e.g., PROJ)",
    )
    addproject_parser.add_argument(
        "--lab",
        help="Lab name (DudaLab, HébertLab, etc.)",
    )
    addproject_parser.add_argument(
        "--path",
        help="Project path",
    )
    addproject_parser.add_argument(
        "--status",
        default="active",
        choices=["active", "paused", "completed"],
        help="Project status (default: active)",
    )
    addproject_parser.add_argument(
        "--description",
        help="Project description",
    )

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Initialize with data directory override if provided
        config = Config(data_dir=args.data_dir)
        TaskLogger.setup(config)

        # If no command provided, launch TUI
        if not args.command:
            try:
                from task_manager.tui.app import TaskManagerApp
                app = TaskManagerApp(config)
                app.run()
                return 0
            except ImportError:
                print("Error: TUI module not yet implemented")
                print("Use 'task <subcommand>' for CLI mode")
                print("Run 'task --help' for available commands")
                return 1

        # CLI mode
        commands = TaskCommands(config)

        # Execute command
        if args.command == "add":
            tags = args.tags.split(",") if args.tags else None
            task = commands.add(
                description=args.description,
                project=args.project,
                task_type=args.task_type,
                priority=args.priority,
                deadline=args.deadline,
                time_estimate=args.time_estimate,
                employer_client=args.employer_client,
                tags=tags,
                notes=args.notes,
            )
            print(f"✓ Task {task.id} added: {task.description}")

        elif args.command == "list":
            tags = args.tags.split(",") if args.tags else None
            output = commands.list(
                status=args.status,
                project=args.project,
                task_type=args.task_type,
                priority=args.priority,
                deadline_before=args.deadline_before,
                tags=tags,
                all_tags=args.all_tags,
                overdue=args.overdue,
                due_today=args.due_today,
                due_this_week=args.due_this_week,
                due_next=args.due_next,
                sort_by=args.sort_by,
                format=args.format,
            )
            print(output)

        elif args.command == "show":
            output = commands.show(args.task_id, format=args.format)
            print(output)

        elif args.command == "update":
            tags = args.tags.split(",") if args.tags else None
            task = commands.update(
                args.task_id,
                description=args.description,
                status=args.status,
                priority=args.priority,
                deadline=args.deadline,
                notes=args.notes,
                task_type=args.task_type,
                employer_client=args.employer_client,
                time_estimate=args.time_estimate,
                tags=tags,
            )
            print(f"✓ Task {task.id} updated")

        elif args.command == "complete":
            task = commands.complete(args.task_id, notes=args.notes)
            print(f"✓ Task {task.id} marked as complete")

        elif args.command == "delete":
            commands.delete(args.task_id, confirm=args.confirm)
            print(f"✓ Task {args.task_id} deleted")

        elif args.command == "log-time":
            task = commands.log_time(
                args.task_id,
                hours=args.hours,
                description=args.description,
                date=args.date,
            )
            print(f"✓ Logged {args.hours}h on task {task.id}")

        elif args.command == "search":
            output = commands.search(args.query, search_in=args.search_in, format=args.format)
            print(output)

        elif args.command == "stats":
            output = commands.stats()
            print(output)

        elif args.command == "time-report":
            output = commands.time_report(
                project=args.project,
                client=args.client,
                start_date=args.start_date,
                end_date=args.end_date,
                group_by=args.group_by,
            )
            print(output)

        elif args.command == "add-project":
            # Auto-generate project ID from name if not provided
            project_id = args.id
            if not project_id:
                import re
                # Convert name to kebab-case ID
                project_id = args.name.lower().replace(" ", "-").replace("_", "-")
                # Remove special characters, keep only alphanumeric and hyphens
                project_id = re.sub(r'[^a-z0-9-]', '', project_id)
                # Remove multiple consecutive hyphens
                project_id = re.sub(r'-+', '-', project_id)
                # Remove leading/trailing hyphens
                project_id = project_id.strip('-')
            
            commands.add_project(
                project_id=project_id,
                name=args.name,
                code=args.code,
                lab=args.lab,
                path=args.path,
                status=args.status,
                description=args.description,
            )
            print(f"✓ Project '{project_id}' ({args.code}) added: {args.name}")

        return 0

    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
