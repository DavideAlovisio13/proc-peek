"""
Command-line interface for proc-peek
"""

import typer
from rich import print
from rich.panel import Panel

app = typer.Typer(add_completion=False, rich_markup_mode="rich")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """[bold cyan]proc‑peek[/] – mini process monitor.[/]
    Run without sub‑command to launch TUI."""
    if ctx.invoked_subcommand is None:
        from .tui import run_tui  # lazy‑import

        run_tui()


@app.command()
def list(
    sort_by: str = typer.Option(
        "cpu", "--sort", "-s", help="Sort by: cpu, memory, name, pid"
    ),
    count: int = typer.Option(10, "--count", "-n", help="Number of processes to show"),
):
    """List top processes in the terminal (no interactive UI)."""
    from .process_info import get_process_list

    print(Panel.fit(f"[bold cyan]Top {count} processes sorted by {sort_by}[/]"))

    processes = get_process_list(sort_by=sort_by)[:count]

    # Print a header
    print(f"{'PID':>7} {'CPU%':>7} {'MEM%':>7} {'NAME':<30}")
    print("─" * 55)

    # Print each process
    for proc in processes:
        print(
            f"{proc['pid']:>7} {proc['cpu_percent']:>6.1f}% {proc['memory_percent']:>6.1f}% "
            f"{proc['name']:<30}"
        )


if __name__ == "__main__":  # pragma: no cover
    app()
