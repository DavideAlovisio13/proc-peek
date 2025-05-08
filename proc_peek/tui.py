"""
Text User Interface for proc-peek
Built with Textual
"""

import time
from typing import List, Dict, Any

from rich.console import RenderableType
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Header, Footer, Static, Button, DataTable, Label
from textual.widgets.data_table import RowKey

from .process_info import (
    get_process_list,
    get_system_info,
    get_process_info,
    format_bytes,
    format_time_delta,
    kill_process,
)


class SystemInfoPanel(Static):
    """Widget to display system information"""

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self.update_timer = 0

    def on_mount(self) -> None:
        self.set_interval(1.0, self.update_system_info)

    def update_system_info(self) -> None:
        """Update the system information display"""
        info = get_system_info()

        # Build rich text for CPU info
        cpu_text = Text(f"CPU: ", style="bold")
        cpu_text.append(f"{info['cpu']['percent']}%")
        cpu_text.append(f" ({info['cpu']['count_logical']} logical cores)")

        # Build rich text for memory info
        memory_text = Text(f"Memory: ", style="bold")
        memory_text.append(
            f"{info['memory']['percent']}% of {format_bytes(info['memory']['total'])}"
        )

        # Build rich text for disk info
        disk_text = Text(f"Disk: ", style="bold")
        disk_text.append(
            f"{info['disk']['percent']}% of {format_bytes(info['disk']['total'])}"
        )

        # Build rich text for uptime
        uptime_text = Text(f"Uptime: ", style="bold")
        uptime_text.append(format_time_delta(info["uptime_seconds"]))

        # Temperature if available
        temp_text = ""
        if info["temperature"] is not None:
            temp_text = f"CPU Temp: [bold]{info['temperature']}°C[/]"

        # Create a panel with all the information
        panel = Panel(
            f"{cpu_text}\n{memory_text}\n{disk_text}\n{uptime_text}\n{temp_text}",
            title="System Info",
            border_style="blue",
        )

        # Update the widget content
        self.update(panel)


class ProcessTable(Static):
    """Widget to display the process table"""

    sort_field = reactive("cpu")
    selected_pid = reactive(-1)

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self.processes: List[Dict[str, Any]] = []

    def on_mount(self) -> None:
        self.set_interval(2.0, self.update_process_list)

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        # Create the header buttons for sorting
        yield Horizontal(
            Button("CPU %", id="sort_cpu", classes="sort_button"),
            Button("Memory %", id="sort_memory", classes="sort_button"),
            Button("Name", id="sort_name", classes="sort_button"),
            Button("PID", id="sort_pid", classes="sort_button"),
            id="sort_buttons",
        )

        # Create the data table
        table = DataTable(id="process_table")
        table.add_column("PID", width=7)
        table.add_column("CPU %", width=7)
        table.add_column("Memory %", width=10)
        table.add_column("Status", width=10)
        table.add_column("Name", width=30)
        yield table

    def update_process_list(self) -> None:
        """Update the process list and refresh the table"""
        # Get sorted process list
        self.processes = get_process_list(sort_by=self.sort_field)

        # Get the table widget
        table = self.query_one("#process_table", DataTable)

        # Clear the table and add rows
        table.clear()

        # Verifica se il processo selezionato esiste ancora
        pid_exists = any(proc["pid"] == self.selected_pid for proc in self.processes)
        if not pid_exists and self.selected_pid > 0:
            # Processo non più esistente, resetta la selezione
            self.selected_pid = -1
            # Aggiorna la vista dei dettagli
            self.app.query_one(ProcessDetail).update_process_detail(-1)

        # Popola la tabella
        for proc in self.processes:
            row_key = str(proc["pid"])
            table.add_row(
                str(proc["pid"]),
                f"{proc['cpu_percent']:.1f}%",
                f"{proc['memory_percent']:.1f}%",
                proc["status"],
                proc["name"],
                key=row_key,
            )

            # Se questa riga è selezionata, evidenziala
            if proc["pid"] == self.selected_pid:
                table.cursor_row = row_key

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses for sorting"""
        button_id = event.button.id
        if button_id:
            sort_type = button_id.replace("sort_", "")
            self.sort_field = sort_type
            self.update_process_list()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the data table"""
        row_key = event.row_key.value
        self.selected_pid = int(row_key)
        self.app.query_one(ProcessDetail).update_process_detail(self.selected_pid)


class ProcessDetail(Static):
    """Widget to display detailed information about a selected process"""

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self.pid: int = -1

    def compose(self) -> ComposeResult:
        yield Static(
            Panel("Select a process to view details", title="Process Detail"),
            id="process_detail_content",
        )
        yield Horizontal(
            Button("Refresh", id="refresh_detail", variant="primary"),
            Button("Kill Process", id="kill_process", variant="error"),
            id="detail_buttons",
        )

    def update_process_detail(self, pid: int) -> None:
        """Update the process detail panel with information about the given PID"""
        self.pid = pid

        if pid <= 0:
            self.query_one("#process_detail_content").update(
                Panel("Select a process to view details", title="Process Detail")
            )
            return

        # Get detailed process info
        info = get_process_info(pid)

        # Format time
        created_time = (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info["created_time"]))
            if info["created_time"] > 0
            else "Unknown"
        )

        # Create detail table
        table = Table(show_header=False, expand=True)
        table.add_column("Property")
        table.add_column("Value")

        table.add_row("PID", str(info["pid"]))
        table.add_row("Name", info["name"])
        table.add_row("Status", info["status"])
        table.add_row("User", info["username"])
        table.add_row("Started", created_time)
        table.add_row("CPU Usage", f"{info['cpu_percent']:.2f}%")
        table.add_row("Memory Usage", f"{info['memory_percent']:.2f}%")
        table.add_row("Memory (RSS)", format_bytes(info["memory_rss"]))
        table.add_row("Memory (VMS)", format_bytes(info["memory_vms"]))

        if info["cmdline"]:
            table.add_row("Command", info["cmdline"])

        if info["exe"]:
            table.add_row("Executable", info["exe"])

        if info["io_read_bytes"] > 0 or info["io_write_bytes"] > 0:
            table.add_row("I/O Read", format_bytes(info["io_read_bytes"]))
            table.add_row("I/O Write", format_bytes(info["io_write_bytes"]))

        # Update the panel
        panel = Panel(
            table,
            title=f"Process Detail - {info['name']} ({info['pid']})",
            border_style="green",
        )

        self.query_one("#process_detail_content").update(panel)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "refresh_detail":
            self.update_process_detail(self.pid)

        elif button_id == "kill_process":
            if self.pid > 0:
                # Get process name
                process_name = ""
                for proc in self.app.query_one(ProcessTable).processes:
                    if proc["pid"] == self.pid:
                        process_name = proc["name"]
                        break

                # Show confirmation dialog
                async def show_dialog():
                    dialog = KillConfirmDialog(self.pid, process_name)
                    result = await self.app.push_screen(dialog)

                    if result and isinstance(result, tuple):
                        action, force = result
                        if action == "terminate":
                            result = kill_process(self.pid, force=force)
                            if result["success"]:
                                self.app.notify(
                                    f"Process {self.pid} terminated", title="Success"
                                )
                                # Refresh the process list
                                self.app.query_one(ProcessTable).update_process_list()
                                # Clear the detail view
                                self.pid = -1
                                self.update_process_detail(-1)
                            else:
                                self.app.notify(
                                    f"Failed to terminate process: {result['error']}",
                                    title="Error",
                                    severity="error",
                                )

                self.app.run_worker(show_dialog())


from textual.containers import Center
from textual.widgets import Button, Label, Static
from textual.screen import ModalScreen


class KillConfirmDialog(ModalScreen):
    """Dialog for confirming process termination"""

    def __init__(self, pid: int, process_name: str):
        super().__init__()
        self.pid = pid
        self.process_name = process_name

    def compose(self) -> ComposeResult:
        yield Center(
            Panel(
                Vertical(
                    Label(f"Are you sure you want to terminate process?"),
                    Label(f"PID: {self.pid} - {self.process_name}", classes="detail"),
                    Horizontal(
                        Button("Cancel", id="cancel", variant="primary"),
                        Button("Terminate", id="terminate", variant="error"),
                        Button("Force Kill", id="force_kill", variant="error"),
                        classes="buttons",
                    ),
                    classes="confirm_dialog",
                ),
                title="Confirm Process Termination",
            ),
            id="confirm_dialog_center",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "cancel":
            self.dismiss(False)
        elif button_id == "terminate":
            self.dismiss(("terminate", False))
        elif button_id == "force_kill":
            self.dismiss(("terminate", True))


class ProcessMonitorApp(App):
    """The main Textual application for proc-peek"""

    CSS = """
/* CSS esistente... */

.confirm_dialog {
    width: 50;
    height: auto;
    padding: 1;
}

.confirm_dialog .detail {
    margin: 1 0;
}

.confirm_dialog .buttons {
    margin-top: 1;
    align-horizontal: center;
}

.confirm_dialog Button {
    margin: 0 1;
}

#confirm_dialog_center {
    align: center middle;
}
"""

    TITLE = "proc-peek: Process Monitor"
    SUB_TITLE = "Press q to quit, ? for help"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app"""
        yield Header()
        yield SystemInfoPanel(id="system_info")
        yield ProcessTable(id="process_table")
        yield ProcessDetail(id="process_detail")
        yield Footer()

    def on_mount(self) -> None:
        """Set up the application"""
        # Make the process table get focus by default
        self.query_one("#process_table").focus()


def update_process_detail(self, pid: int) -> None:
    """Update the process detail panel with information about the given PID"""
    self.pid = pid

    if pid <= 0:
        self.query_one("#process_detail_content").update(
            Panel("Select a process to view details", title="Process Detail")
        )
        return

    # Get detailed process info
    info = get_process_info(pid)

    # Controlla se il processo è accessibile
    if info["name"] == "[Process not available]":
        self.query_one("#process_detail_content").update(
            Panel(
                "Process information not available.\nThe process may no longer exist or you may not have permission to access it.",
                title=f"Process Detail - PID {pid}",
                border_style="red",
            )
        )
        return


def run_tui():
    """Run the Textual UI application"""
    app = ProcessMonitorApp()
    app.run()


if __name__ == "__main__":
    run_tui()
