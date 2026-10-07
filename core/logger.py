"""
ISKOM AI-OS Activity Audit Trail Logger & Monitoring Engine
Mencatat 10 parameter audit untuk setiap tindakan AI ke dalam file JSONL dan memori:
1. Waktu (Timestamp)
2. User
3. Agent
4. Input
5. Keputusan (Intent & Routing)
6. Tool (Tools dipanggil)
7. Action (Aksi yang diambil)
8. Result (Hasil/Respon)
9. Error (Pesan error jika ada)
10. Approval (Status dan rincian approval)
"""

import os
import json
import datetime
from typing import Dict, Any, List, Optional
import uuid


class ActivityLogger:
    """Mesin pencatat audit trail aktivitas AI dan kalkulator metrik monitoring"""

    def __init__(self, log_dir: Optional[str] = None):
        if not log_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(base_dir, "logs")
        self.log_dir = log_dir
        self.log_file = os.path.join(self.log_dir, "activity_logs.jsonl")
        self._ensure_dir()
        self.memory_logs: List[Dict[str, Any]] = []

    def _ensure_dir(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

    def log_action(
        self,
        user: str,
        agent_id: str,
        agent_name: str,
        user_input: str,
        keputusan: str,
        tools_called: List[str],
        action: str,
        result: str,
        error: Optional[str] = None,
        approval_required: bool = False,
        approval_details: Optional[Dict[str, Any]] = None,
        latency_ms: int = 0
    ) -> Dict[str, Any]:
        """Mencatat 1 log aktivitas lengkap dengan 10 atribut wajib"""
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        log_id = f"LOG-{uuid.uuid4().hex[:10].upper()}"

        record = {
            "log_id": log_id,
            "waktu": timestamp,
            "user": user,
            "agent": {
                "id": agent_id,
                "name": agent_name
            },
            "input": user_input,
            "keputusan": keputusan,
            "tool": tools_called,
            "action": action,
            "result": result,
            "error": error,
            "approval": {
                "required": approval_required,
                "details": approval_details or {}
            },
            "latency_ms": latency_ms,
            "status": "ERROR" if error else ("PENDING_APPROVAL" if approval_required else "SUCCESS")
        }

        # 1. Simpan ke buffer memori
        self.memory_logs.append(record)

        # 2. Append ke file JSON Lines (Persisten)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[!] Warning: Gagal menulis log audit ke disk: {e}")

        return record

    def get_recent_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Mengambil daftar log terbaru untuk monitoring"""
        return list(reversed(self.memory_logs[-limit:]))

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Mengambil seluruh aksi yang saat ini tertahan membutuhkan persetujuan Owner"""
        return [
            log for log in self.memory_logs
            if log["approval"]["required"] and log["status"] == "PENDING_APPROVAL"
        ]

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Menghitung ringkasan KPI monitoring real-time untuk dashboard Owner"""
        total = len(self.memory_logs)
        if total == 0:
            return {
                "total_requests": 0,
                "success_rate": 100.0,
                "pending_approvals": 0,
                "error_count": 0,
                "avg_latency_ms": 0,
                "agent_distribution": {}
            }

        success_count = sum(1 for l in self.memory_logs if l["status"] in ["SUCCESS", "PENDING_APPROVAL"])
        error_count = sum(1 for l in self.memory_logs if l["status"] == "ERROR")
        pending_approvals = sum(1 for l in self.memory_logs if l["status"] == "PENDING_APPROVAL")
        avg_latency = sum(l["latency_ms"] for l in self.memory_logs) / total

        # Distribusi beban per agent
        agent_dist: Dict[str, int] = {}
        for l in self.memory_logs:
            ag_id = l["agent"]["id"]
            agent_dist[ag_id] = agent_dist.get(ag_id, 0) + 1

        return {
            "total_requests": total,
            "success_rate": round((success_count / total) * 100, 1),
            "pending_approvals": pending_approvals,
            "error_count": error_count,
            "avg_latency_ms": round(avg_latency, 1),
            "agent_distribution": agent_dist
        }
