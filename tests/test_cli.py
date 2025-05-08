"""
Tests for the CLI module
"""

import pytest
from typer.testing import CliRunner
from proc_peek.cli import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing"""
    return CliRunner()


def test_app_help(runner):
    """Test the help message is displayed correctly"""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "proc‑peek" in result.stdout
    assert "mini process monitor" in result.stdout


def test_list_command(runner):
    """Test the list command works"""
    result = runner.invoke(app, ["list", "--count", "5"])
    assert result.exit_code == 0
    assert "Top 5 processes" in result.stdout

    # Should have a header line for the table
    assert "PID" in result.stdout
    assert "CPU%" in result.stdout
    assert "MEM%" in result.stdout
    assert "NAME" in result.stdout


def test_list_command_with_sort(runner):
    """Test the list command with sorting options"""
    # Test sorting by memory
    result = runner.invoke(app, ["list", "--sort", "memory"])
    assert result.exit_code == 0
    assert "sorted by memory" in result.stdout

    # Test sorting by name
    result = runner.invoke(app, ["list", "--sort", "name"])
    assert result.exit_code == 0
    assert "sorted by name" in result.stdout

    # Test sorting by pid
    result = runner.invoke(app, ["list", "--sort", "pid"])
    assert result.exit_code == 0
    assert "sorted by pid" in result.stdout
