"""
ISKOM AI-OS Agent State Tracker
Melacak status real-time setiap agen untuk visualisasi Pixel Office:
  OFFLINE          -> Kamar Tidur
  IDLE             -> Lounge / Pantry
  WORKING          -> Ruang Kerja (Inventory -> Gudang)
  WAITING_APPROVAL -> Antre di Ruang Owner
  HUMAN_NEEDED     -> Ruang Owner (OTP/CAPTCHA, butuh manusia)
  ERROR            -> Ruang ER
"""

import time
import uuid
from typing import Dict, Any, List, Optional

# Durasi minimum animasi "bekerja" agar terlihat di dashboard (proses asli ~ms)
MIN_WORKING_SECONDS = 4.0
# Status error otomatis kembali ke IDLE setelah durasi ini
ERROR_DISPLAY_SECONDS = 20.0

# Roster 10 agen sesuai AI Organization Chart (docs/02_ai_organization_chart.md)
AGENT_ROSTER: List[Dict[str, str]] = [
    {"id": "AGENT-MGR-01", "name": "AI Business Manager", "short": "Manager", "role": "Executive Orchestrator"},
    {"id": "AGENT-SLS-01", "name": "Sales & Rental Agent", "short": "Sales", "role": "Rental Sales Consultant"},
    {"id": "AGENT-INV-01", "name": "Inventory & Unit Agent", "short": "Inventory", "role": "Warehouse & Stock Controller"},
    {"id": "AGENT-CS-01", "name": "Customer Service Agent", "short": "CS", "role": "Helpdesk & Customer Care"},
    {"id": "AGENT-FIN-01", "name": "Finance & Invoicing Agent", "short": "Finance", "role": "Billing & Invoicing"},
    {"id": "AGENT-KPI-01", "name": "KPI & Executive Agent", "short": "KPI", "role": "Executive Reporting"},
    {"id": "AGENT-MKT-01", "name": "Marketing Agent", "short": "Marketing", "role": "Campaign & Content"},
    {"id": "AGENT-PRS-01", "name": "Prospecting Agent", "short": "Prospect", "role": "Lead Generation"},
    {"id": "AGENT-OPS-01", "name": "Rental Operation Agent", "short": "Operation", "role": "Delivery & Pickup"},
    {"id": "AGENT-COL-01", "name": "Collection Agent", "short": "Collection", "role": "Payment Collection"},
]

ROOM_BY_STATUS = {
    "OFFLINE": "dorm",
    "SLEEPING": "dorm",
    "IDLE": "lounge",
    "WORKING": "work",
    "WAITING_APPROVAL": "owner",
    "HUMAN_NEEDED": "owner",
    "ERROR": "er",
}

FLOOR_BY_ROOM = {
    "work": 1,
    "meeting": 1,
    "owner": 1,
    "warehouse": 1,
    "lounge": 1,
    "pantry": 1,
    "game": 1,
    "outdoor": 1,
    "server": 1,
    "er": 1,
    "dorm": 2,
    "bedroom": 2,
    "balcony": 2,
    "lesehan": 2,
    "restroom": 2,
}


class AgentStateTracker:
    """Penyimpan status hidup seluruh agen + antrean approval Owner"""

    def __init__(self, implemented_agent_ids: List[str]):
        self.implemented = set(implemented_agent_ids)
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.approvals: List[Dict[str, Any]] = []
        now = time.time()
        for meta in AGENT_ROSTER:
            built = meta["id"] in self.implemented
            self.agents[meta["id"]] = {
                **meta,
                "implemented": built,
                "powered": built,
                "sleeping": False,
                "status": "IDLE" if built else "OFFLINE",
                "task": None,
                "tools": [],
                "last_reply": None,
                "busy_until": 0.0,
                "error_until": 0.0,
                "since": now,
                "tasks_done": 0,
            }

    # ------------------------------------------------------------------ queries
    def is_online(self, agent_id: str) -> bool:
        ag = self.agents.get(agent_id)
        return bool(ag and ag["powered"])

    def _effective_status(self, ag: Dict[str, Any], now: float) -> str:
        if not ag["powered"]:
            return "OFFLINE"
        if ag["busy_until"] > now:
            return "WORKING"
        if ag.get("sleeping", False):
            return "SLEEPING"
        if ag["status"] == "ERROR" and ag["error_until"] <= now:
            ag["status"] = "IDLE"
            ag["since"] = now
        if ag["status"] in ("WAITING_APPROVAL", "HUMAN_NEEDED", "ERROR"):
            return ag["status"]
        return "IDLE"

    def snapshot(self) -> Dict[str, Any]:
        now = time.time()
        agents_out = []
        for ag in self.agents.values():
            status = self._effective_status(ag, now)
            room = ROOM_BY_STATUS.get(status, "lounge")
            floor = FLOOR_BY_ROOM.get(room, 1)
            agents_out.append({
                "id": ag["id"],
                "name": ag["name"],
                "short": ag["short"],
                "role": ag["role"],
                "implemented": ag["implemented"],
                "powered": ag["powered"],
                "sleeping": ag.get("sleeping", False),
                "status": status,
                "room": room,
                "floor": floor,
                "task": ag["task"],
                "tools": ag["tools"],
                "last_reply": ag["last_reply"],
                "tasks_done": ag["tasks_done"],
                "since": ag["since"],
            })
        pending = [a for a in self.approvals if a["state"] == "PENDING"]
        floor1_count = sum(1 for a in agents_out if a["floor"] == 1 and a["powered"])
        floor2_count = sum(1 for a in agents_out if a["floor"] == 2 or not a["powered"])
        return {
            "server_time": now,
            "agents": agents_out,
            "approvals": pending,
            "summary": {
                "online": sum(1 for a in agents_out if a["powered"]),
                "total": len(agents_out),
                "working": sum(1 for a in agents_out if a["status"] == "WORKING"),
                "sleeping": sum(1 for a in agents_out if a["status"] == "SLEEPING"),
                "floor1": floor1_count,
                "floor2": floor2_count,
                "pending_approvals": len(pending),
            },
        }

    # ---------------------------------------------------------------- mutations
    def mark_working(self, agent_id: str, task: str):
        ag = self.agents.get(agent_id)
        if not ag:
            return
        now = time.time()
        ag["task"] = task
        ag["tools"] = []
        ag["busy_until"] = now + MIN_WORKING_SECONDS
        ag["since"] = now

    def mark_result(self, agent_id: str, status: str, tools: List[str], reply: str,
                    task: str, approval_details: Optional[Dict[str, Any]] = None):
        ag = self.agents.get(agent_id)
        if not ag:
            return
        now = time.time()
        ag["tools"] = list(tools or [])
        ag["last_reply"] = reply
        ag["tasks_done"] += 1

        if status == "PENDING_APPROVAL":
            ag["status"] = "WAITING_APPROVAL"
            details = approval_details or {}
            self.approvals.append({
                "approval_id": details.get("approval_id") or f"APV-{uuid.uuid4().hex[:6].upper()}",
                "agent_id": agent_id,
                "agent_name": ag["name"],
                "task": task,
                "category": details.get("category", "APPROVAL_REQUEST"),
                "total": details.get("total"),
                "summary": reply,
                "state": "PENDING",
                "created_at": now,
            })
        elif status == "HUMAN_INTERVENTION_REQUIRED":
            ag["status"] = "HUMAN_NEEDED"
        elif status in ("ERROR", "BLOCKED_BY_RULE"):
            ag["status"] = "ERROR"
            ag["error_until"] = now + MIN_WORKING_SECONDS + ERROR_DISPLAY_SECONDS
        else:
            ag["status"] = "IDLE"
        ag["since"] = now

    def resolve_approval(self, approval_id: str, decision: str) -> Optional[Dict[str, Any]]:
        """Owner memutuskan APPROVED / REJECTED; agen kembali ke lounge bila antreannya habis"""
        target = next((a for a in self.approvals
                       if a["approval_id"] == approval_id and a["state"] == "PENDING"), None)
        if not target:
            return None
        target["state"] = decision
        target["decided_at"] = time.time()
        agent_id = target["agent_id"]
        still_pending = any(a["agent_id"] == agent_id and a["state"] == "PENDING" for a in self.approvals)
        ag = self.agents.get(agent_id)
        if ag and not still_pending and ag["status"] == "WAITING_APPROVAL":
            ag["status"] = "IDLE"
            ag["since"] = time.time()
        return target

    def clear_human_needed(self, agent_id: str):
        ag = self.agents.get(agent_id)
        if ag and ag["status"] == "HUMAN_NEEDED":
            ag["status"] = "IDLE"
            ag["since"] = time.time()

    def set_power(self, agent_id: str, on: bool) -> Dict[str, Any]:
        ag = self.agents.get(agent_id)
        if not ag:
            raise KeyError(f"Agen '{agent_id}' tidak terdaftar")
        if on and not ag["implemented"]:
            raise ValueError(f"{ag['name']} belum dibangun (fase berikutnya), tidak bisa diaktifkan")
        ag["powered"] = on
        ag["busy_until"] = 0.0
        ag["sleeping"] = False
        ag["status"] = "IDLE" if on else "OFFLINE"
        ag["since"] = time.time()
        return {"agent_id": agent_id, "powered": on}

    def sleep_all(self) -> Dict[str, Any]:
        """Kirim semua agen aktif yang sedang idle ke dorm kamar tidur (Lantai 2)"""
        count = 0
        now = time.time()
        for ag in self.agents.values():
            if ag["powered"] and ag["status"] in ("IDLE", "SLEEPING"):
                ag["sleeping"] = True
                ag["since"] = now
                count += 1
        return {"status": "SUCCESS", "sleeping_count": count, "mode": "SLEEP"}

    def wake_all(self) -> Dict[str, Any]:
        """Bangunkan semua agen dari tidur kembali ke Lantai 1 (standby / IDLE)"""
        count = 0
        now = time.time()
        for ag in self.agents.values():
            if ag["powered"] and ag.get("sleeping", False):
                ag["sleeping"] = False
                ag["since"] = now
                count += 1
        return {"status": "SUCCESS", "woken_count": count, "mode": "AWAKE"}

    def toggle_sleep_all(self) -> Dict[str, Any]:
        """Toggle antara tidurkan semua agen idle vs bangunkan semua agen"""
        any_sleeping = any(ag.get("sleeping", False) for ag in self.agents.values() if ag["powered"])
        if any_sleeping:
            return self.wake_all()
        return self.sleep_all()

    def toggle_agent_sleep(self, agent_id: str) -> Dict[str, Any]:
        """Toggle tidur untuk 1 agen spesifik"""
        ag = self.agents.get(agent_id)
        if not ag:
            raise KeyError(f"Agen '{agent_id}' tidak terdaftar")
        if not ag["powered"]:
            raise ValueError(f"{ag['name']} sedang offline")
        ag["sleeping"] = not ag.get("sleeping", False)
        ag["since"] = time.time()
        return {"agent_id": agent_id, "sleeping": ag["sleeping"]}

