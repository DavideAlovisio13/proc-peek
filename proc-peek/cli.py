import typer
from rich import print
from rich.panel import Panel

app = typer.Typer(add_completion=False, rich_markup_mode="rich")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    \"\"\"[bold cyan]proc‑peek[/] – mini process monitor.[/]\nRun without sub‑command to launch TUI.\"\"\"
    if ctx.invoked_subcommand is None:
        from .tui import run_tui  # lazy‑import
        run_tui()

if __name__ == \"__main__\":  # pragma: no cover
    app()
