"""
Process information gathering module
"""

import os
import time
import psutil
from typing import List, Dict, Any, Optional


def get_process_info(pid: int) -> Dict[str, Any]:
    """Get detailed information about a specific process"""
    try:
        proc = psutil.Process(pid)

        # Basic info
        info = {
            "pid": pid,
            "name": proc.name(),
            "status": proc.status(),
            "username": proc.username(),
            "cpu_percent": proc.cpu_percent(),
            "memory_percent": proc.memory_percent(),
            "created_time": proc.create_time(),
        }

        # Add more detailed info when available
        try:
            info["cmdline"] = " ".join(proc.cmdline())
        except (psutil.AccessDenied, psutil.ZombieProcess):
            info["cmdline"] = "[Access Denied]"

        try:
            info["exe"] = proc.exe()
        except (psutil.AccessDenied, psutil.ZombieProcess):
            info["exe"] = "[Access Denied]"

        # Get memory info
        try:
            mem_info = proc.memory_info()
            info["memory_rss"] = mem_info.rss
            info["memory_vms"] = mem_info.vms
        except (psutil.AccessDenied, psutil.ZombieProcess):
            info["memory_rss"] = 0
            info["memory_vms"] = 0

        # IO info
        try:
            io_counters = proc.io_counters()
            info["io_read_bytes"] = io_counters.read_bytes
            info["io_write_bytes"] = io_counters.write_bytes
        except (psutil.AccessDenied, psutil.ZombieProcess, AttributeError):
            info["io_read_bytes"] = 0
            info["io_write_bytes"] = 0

        return info
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return {
            "pid": pid,
            "name": "[Process not available]",
            "status": "unknown",
            "username": "unknown",
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "created_time": 0,
            "cmdline": "",
            "exe": "",
            "memory_rss": 0,
            "memory_vms": 0,
            "io_read_bytes": 0,
            "io_write_bytes": 0,
        }


def get_process_list(sort_by: str = "cpu") -> List[Dict[str, Any]]:
    """
    Get a list of all running processes with basic information

    Args:
        sort_by: Field to sort by - "cpu", "memory", "name", or "pid"

    Returns:
        List of process information dictionaries
    """
    # Get all process IDs
    processes = []

    # First pass to collect processes and start CPU monitoring
    for pid in psutil.pids():
        try:
            proc = psutil.Process(pid)
            # Start CPU percent measurement
            proc.cpu_percent()
            processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Small delay to get accurate CPU measurements
    time.sleep(0.1)

    # Second pass to collect info
    result = []
    for proc in processes:
        try:
            pid = proc.pid
            info = {
                "pid": pid,
                "name": proc.name(),
                "cpu_percent": proc.cpu_percent(),
                "memory_percent": proc.memory_percent(),
                "status": proc.status(),
            }
            result.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort the result
    if sort_by == "cpu":
        result.sort(key=lambda x: x["cpu_percent"], reverse=True)
    elif sort_by == "memory":
        result.sort(key=lambda x: x["memory_percent"], reverse=True)
    elif sort_by == "name":
        result.sort(key=lambda x: x["name"].lower())
    elif sort_by == "pid":
        result.sort(key=lambda x: x["pid"])

    return result


def get_system_info() -> Dict[str, Any]:
    """Get overall system information"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage("/")

    if hasattr(psutil, "sensors_temperatures") and callable(
        getattr(psutil, "sensors_temperatures")
    ):
        try:
            temps = psutil.sensors_temperatures()
            # Just get the first temperature reading if available
            temperature = (
                next(iter(next(iter(temps.values()))), None) if temps else None
            )
            temp_value = temperature.current if temperature else None
        except:
            temp_value = None
    else:
        temp_value = None

    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time

    return {
        "cpu": {
            "percent": cpu_percent,
            "count_logical": psutil.cpu_count(),
            "count_physical": psutil.cpu_count(logical=False) or 1,
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
        },
        "swap": {
            "total": swap.total,
            "used": swap.used,
            "percent": swap.percent,
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "percent": disk.percent,
        },
        "temperature": temp_value,
        "boot_time": boot_time,
        "uptime_seconds": uptime_seconds,
    }


def format_bytes(bytes_value: int) -> str:
    """Format bytes as human-readable string with units"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_time_delta(seconds: float) -> str:
    """Format seconds as days, hours, minutes, seconds"""
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def kill_process(pid: int) -> bool:
    """
    Kill a process by PID

    Returns:
        True if successful, False otherwise
    """
    try:
        proc = psutil.Process(pid)
        proc.kill()
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False
