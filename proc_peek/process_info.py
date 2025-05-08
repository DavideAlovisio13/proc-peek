"""
Process information gathering module
"""

import os
import time
import logging
import psutil
from typing import List, Dict, Any, Optional

# Configurazione logging di base
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("proc_peek")


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
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Usa il percorso appropriato in base al sistema operativo
        if os.name == "nt":  # Windows
            disk_path = os.environ.get("SYSTEMDRIVE", "C:")
        else:  # Linux, macOS, ecc.
            disk_path = "/"

        try:
            disk = psutil.disk_usage(disk_path)
        except Exception as e:
            logger.error(f"Error getting disk usage for {disk_path}: {e}")
            # Valori predefiniti se non è possibile ottenere l'uso del disco
            disk = type("obj", (object,), {"total": 0, "used": 0, "percent": 0})

        # Ottieni le temperature se disponibili
        temp_value = None
        if hasattr(psutil, "sensors_temperatures") and callable(
            getattr(psutil, "sensors_temperatures")
        ):
            try:
                temps = psutil.sensors_temperatures()
                # Prendi la prima lettura di temperatura disponibile
                if temps and len(temps) > 0:
                    first_sensor = next(iter(temps.values()), [])
                    if first_sensor and len(first_sensor) > 0:
                        temperature = first_sensor[0]
                        temp_value = (
                            temperature.current
                            if hasattr(temperature, "current")
                            else None
                        )
            except Exception as e:
                logger.error(f"Error getting temperature info: {e}")

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
                "path": disk_path,  # Aggiunto il percorso
            },
            "temperature": temp_value,
            "boot_time": boot_time,
            "uptime_seconds": uptime_seconds,
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        # Restituisci dati di fallback se qualcosa va storto
        return {
            "cpu": {"percent": 0, "count_logical": 0, "count_physical": 0},
            "memory": {"total": 0, "available": 0, "percent": 0, "used": 0},
            "swap": {"total": 0, "used": 0, "percent": 0},
            "disk": {"total": 0, "used": 0, "percent": 0, "path": "/"},
            "temperature": None,
            "boot_time": 0,
            "uptime_seconds": 0,
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


def kill_process(pid: int, force: bool = False) -> Dict[str, Any]:
    """
    Kill or terminate a process by PID

    Args:
        pid: Process ID to kill
        force: If True, use kill() instead of terminate()

    Returns:
        Dictionary with success status and error message if any
    """
    try:
        proc = psutil.Process(pid)

        if force:
            proc.kill()
        else:
            proc.terminate()

        return {"success": True, "error": None}
    except psutil.NoSuchProcess:
        return {"success": False, "error": "Process does not exist"}
    except psutil.AccessDenied:
        return {
            "success": False,
            "error": "Access denied (try running as administrator)",
        }
    except psutil.ZombieProcess:
        return {"success": False, "error": "Process is a zombie process"}
    except Exception as e:
        return {"success": False, "error": str(e)}
