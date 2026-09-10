"""
IT Helpdesk Agent Tools:
1. Incident Ticket System (Create, Lookup, Escalate)
2. Live System Diagnostic Scanner
3. Knowledge Base Tool Wrapper
"""

import os
import time
import json
import random
import shutil
import platform
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

TICKETS_FILE = os.path.join(os.path.dirname(__file__), "tickets.json")


def _load_tickets() -> List[Dict[str, Any]]:
    """Load tickets from local storage."""
    if os.path.exists(TICKETS_FILE):
        try:
            with open(TICKETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_tickets(tickets: List[Dict[str, Any]]) -> None:
    """Save tickets to local storage."""
    with open(TICKETS_FILE, "w", encoding="utf-8") as f:
        json.dump(tickets, f, indent=2)


def create_ticket(
    title: str,
    description: str,
    category: str = "General IT",
    priority: str = "Medium",
    user_name: str = "Employee",
) -> Dict[str, Any]:
    """
    Create a new IT incident support ticket.
    Priority options: Low, Medium, High, Critical
    """
    tickets = _load_tickets()
    ticket_number = random.randint(1000, 9999)
    ticket_id = f"INC-2026-{ticket_number}"

    new_ticket = {
        "ticket_id": ticket_id,
        "title": title,
        "description": description,
        "category": category,
        "priority": priority,
        "status": "Open",
        "user_name": user_name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "assigned_to": "Tier-1 IT Automated Queue",
        "notes": ["Ticket automatically created by AI IT Helpdesk Agent."],
    }

    tickets.insert(0, new_ticket)
    _save_tickets(tickets)
    return new_ticket


def get_all_tickets() -> List[Dict[str, Any]]:
    """Retrieve all tickets."""
    return _load_tickets()


def get_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Find ticket by ID."""
    tickets = _load_tickets()
    for t in tickets:
        if t["ticket_id"].upper() == ticket_id.upper():
            return t
    return None


def escalate_ticket(ticket_id: str, reason: str) -> Dict[str, Any]:
    """Escalate a ticket to Tier-2 Senior IT Support."""
    tickets = _load_tickets()
    for t in tickets:
        if t["ticket_id"].upper() == ticket_id.upper():
            t["status"] = "Escalated"
            t["priority"] = "Critical"
            t["assigned_to"] = "Tier-2 Incident Response Team (Human Engineer)"
            t["notes"].append(f"Escalation Reason: {reason} at {datetime.now().strftime('%H:%M:%S')}")
            _save_tickets(tickets)
            return {"success": True, "ticket": t}
    return {"success": False, "error": f"Ticket {ticket_id} not found."}


def run_system_diagnostics() -> Dict[str, Any]:
    """
    Executes live local host diagnostic checks (Disk, Memory, Network ping, OS status).
    Safe, non-destructive read-only system assessment.
    """
    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "os_platform": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "hostname": platform.node(),
    }

    # 1. Disk Space Check
    try:
        total, used, free = shutil.disk_usage("C:\\" if os.name == "nt" else "/")
        total_gb = round(total / (1024 ** 3), 1)
        used_gb = round(used / (1024 ** 3), 1)
        free_gb = round(free / (1024 ** 3), 1)
        free_pct = round((free / total) * 100, 1)

        results["disk"] = {
            "drive": "C:",
            "total_gb": total_gb,
            "used_gb": used_gb,
            "free_gb": free_gb,
            "free_pct": free_pct,
            "status": "Healthy" if free_pct >= 15 else "Warning (Low Disk Space)",
        }
    except Exception as e:
        results["disk"] = {"error": str(e)}

    # 2. Network Ping Latency (Google DNS / Gateway)
    try:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        ping_cmd = ["ping", param, "1", "8.8.8.8"]
        res = subprocess.run(ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        if res.returncode == 0:
            results["network"] = {
                "internet_reachability": "Connected 🟢",
                "target": "8.8.8.8 (Google DNS)",
                "status": "Online",
            }
        else:
            results["network"] = {
                "internet_reachability": "Offline / Packet Loss 🔴",
                "status": "Offline / High Latency",
            }
    except Exception as e:
        results["network"] = {
            "internet_reachability": "Timeout / Unreachable ⚠️",
            "error": str(e),
        }

    # 3. Overall Health Rating
    is_disk_ok = results.get("disk", {}).get("free_pct", 100) >= 15
    is_net_ok = "Connected" in results.get("network", {}).get("internet_reachability", "")

    if is_disk_ok and is_net_ok:
        results["health_summary"] = "✅ System Health: Normal (No immediate hardware/network fault detected)"
    else:
        results["health_summary"] = "⚠️ System Health: Issues Detected (Review disk space or network adapter)"

    return results
