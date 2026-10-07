"""
ISKOM AI OPERATING SYSTEM — LOCAL WEB SERVER & REST API
=======================================================
Menyajikan Pixel Office Dashboard & REST API untuk interaksi nyata dengan CoreOrchestrator.
Port Default: 8080 (http://localhost:8080)

Halaman:
  /           -> office.html     (Pixel Office: agen pindah ruangan sesuai status)
  /classic    -> dashboard.html  (Dashboard klasik)

API:
  GET  /api/agents/state       -> status seluruh agen + antrean approval
  POST /api/agents/power       -> {"agent_id": "...", "on": true|false}
  POST /api/agents/resolve     -> {"agent_id": "..."}  (Owner menangani OTP/CAPTCHA)
  POST /api/chat               -> {"message": "...", "user_id": "..."}
  POST /api/approve            -> {"approval_id": "...", "action": "APPROVED"|"REJECTED"}
  GET  /api/logs               -> 25 audit log terakhir
  GET  /api/kpi                -> ringkasan KPI
"""

import os
import sys
import json
import asyncio
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from core.orchestrator import CoreOrchestrator

orchestrator = CoreOrchestrator()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "logs", "activity_logs.jsonl")


def read_logs():
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except Exception:
                        pass
    return logs


class AIOSRequestHandler(SimpleHTTPRequestHandler):
    """Handler HTTP: static file + REST API AI-OS"""

    def log_message(self, fmt, *args):
        # Redam log polling dan favicon agar konsol tidak banjir
        try:
            first_arg = str(args[0]) if args else ""
            if "/api/agents/state" in first_arg or "favicon.ico" in first_arg:
                return
        except Exception:
            pass
        super().log_message(fmt, *args)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    # ------------------------------------------------------------------ helpers
    def _json(self, payload, code=200):
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(raw or "{}")

    # --------------------------------------------------------------------- GET
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        dist_dir = os.path.join(BASE_DIR, "ruang-web", "dist")

        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        # Serving static asset dari bundle resmi Ruang
        if path.startswith("/assets/") and os.path.isdir(dist_dir):
            asset_path = os.path.join(dist_dir, path.lstrip("/"))
            if os.path.isfile(asset_path):
                ext = os.path.splitext(asset_path)[1]
                content_type = "text/javascript" if ext == ".js" else ("text/css" if ext == ".css" else "application/octet-stream")
                with open(asset_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "public, max-age=31536000")
                self.end_headers()
                self.wfile.write(content)
                return

        if path in ("/", "/index.html", "/ruang"):
            if os.path.isfile(os.path.join(dist_dir, "index.html")):
                with open(os.path.join(dist_dir, "index.html"), "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(content)
                return
            self.path = "/office.html"
            return super().do_GET()

        if path in ("/standalone", "/office"):
            self.path = "/office.html"
            return super().do_GET()
        if path == "/classic":
            self.path = "/dashboard.html"
            return super().do_GET()
        if path == "/api/health":
            return self.handle_get_health()
        if path == "/api/access":
            return self._json({"enabled": False, "rememberDays": 30, "minLength": 6})
        if path == "/api/profile-lock":
            return self._json({"enabled": False, "agents": [], "unlocked": []})
        if path == "/api/agents/state":
            return self._json(orchestrator.state.snapshot())
        if path == "/api/office":
            return self.handle_get_office()
        if path == "/api/activity":
            return self.handle_get_activity()
        if path == "/api/channels":
            return self.handle_get_channels()
        if path == "/api/dashboard":
            return self.handle_get_dashboard()
        if path == "/api/usage":
            return self.handle_get_usage()
        if path == "/api/tasks":
            return self.handle_get_tasks()
        if path == "/api/calendar":
            return self.handle_get_calendar()
        if path == "/api/runtime":
            return self.handle_get_runtime()
        if path == "/api/memory":
            return self.handle_get_memory()
        if path.startswith("/api/folders/") and "/list" in path:
            parts = [p for p in path.split("/") if p]
            # Expected parts: ['api', 'folders', '<profile>', 'list']
            if len(parts) >= 4:
                profile = urllib.parse.unquote(parts[2])
                parsed = urllib.parse.urlparse(self.path)
                q = urllib.parse.parse_qs(parsed.query)
                sub_path = q.get("path", [""])[0]
                return self.handle_get_folder_list(profile, sub_path)
        if path.startswith("/api/folders/") and "/file" in path:
            parts = [p for p in path.split("/") if p]
            # Expected parts: ['api', 'folders', '<profile>', 'file']
            if len(parts) >= 4:
                profile = urllib.parse.unquote(parts[2])
                parsed = urllib.parse.urlparse(self.path)
                q = urllib.parse.parse_qs(parsed.query)
                file_path = q.get("path", [""])[0]
                return self.handle_get_folder_file(profile, file_path)
        if path == "/api/folders" or path == "/api/folders/":
            return self.handle_get_folders()
        if path == "/api/knowledge":
            return self.handle_get_knowledge()
        if path == "/api/command-log":
            return self.handle_get_command_log()
        if path == "/api/logs":
            return self.handle_get_logs()
        if path == "/api/kpi":
            return self.handle_get_kpi()
        return super().do_GET()

    def handle_get_health(self):
        import datetime
        return self._json({
            "ok": True,
            "apiVersion": 12,
            "system": "ISKOM AI-OS Virtual Office",
            "startedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def handle_get_tasks(self):
        import datetime
        logs = read_logs()[-15:]
        tasks = []
        for idx, l in enumerate(logs):
            tasks.append({
                "id": f"TSK-{idx+1:03d}",
                "title": l.get("user_input") or "Tugas Otomasi",
                "status": "done" if l.get("status") == "SUCCESS" else "in_progress",
                "assignee": l.get("agent_id") or "AGENT-MGR-01"
            })
        return self._json({
            "tasks": {"availability": "available", "data": tasks},
            "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def handle_get_calendar(self):
        import datetime
        return self._json({
            "jobs": {
                "availability": "available",
                "data": [
                    {"name": "Daily Sync Inventory", "schedule": "0 0 * * *", "agent": "AGENT-INV-01", "status": "active"},
                    {"name": "Monthly Billing Cycle", "schedule": "0 0 1 * *", "agent": "AGENT-FIN-01", "status": "active"}
                ]
            },
            "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def handle_get_runtime(self):
        import datetime
        snap = orchestrator.state.snapshot()
        agents = snap["agents"]
        return self._json({
            "profiles": {
                "availability": "available",
                "data": [{"name": a["short"], "model": "gemini-1.5-flash", "gateway": "Running" if a["powered"] else "Stopped"} for a in agents]
            },
            "openCode": {"availability": "available", "data": "Ready"},
            "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def handle_get_memory(self):
        import datetime
        snap = orchestrator.state.snapshot()
        agents = snap["agents"]
        agent_memories = []
        for a in agents:
            agent_memories.append({
                "profile": a["id"],
                "label": a["name"],
                "path": f"agents/{a['id'].lower().replace('-', '_')}.py",
                "kind": "hermes",
                "available": True,
                "soul": {
                    "name": "SOUL.md",
                    "path": "SOUL.md",
                    "exists": True,
                    "content": f"# IDENTITAS AGEN\nNama: {a['name']} ({a['id']})\nRole: {a['role']}\nOrganisasi: CV ISKOM (Rental Laptop & IT Solusindo)\nStatus: Operational"
                },
                "memory": {
                    "name": "MEMORY.md",
                    "path": "MEMORY.md",
                    "exists": True,
                    "entries": [
                        f"Peran Utama: {a['role']}",
                        "SOP: Diskon sewa maksimal 10% tanpa approval Owner ISKOM",
                        "Wajib verifikasi unit di database inventaris fisik sebelum menerbitkan penawaran",
                        "Intervensi Keamanan: Dilarang menangani kode OTP SMS atau CAPTCHA secara otonom"
                    ],
                    "limit": 100,
                    "used": 4,
                    "percent": 4
                },
                "user": {
                    "name": "USER.md",
                    "path": "USER.md",
                    "exists": True,
                    "entries": [
                        "Nama Owner: Fabian (Direktur CV ISKOM)",
                        "Aturan Eskalasi: Nilai transaksi >= Rp 25.000.000 dan diskon > 10% wajib persetujuan Owner"
                    ],
                    "limit": 50,
                    "used": 2,
                    "percent": 4
                },
                "contextFiles": [
                    {
                        "name": "sop_rental.md",
                        "path": "knowledge/sop_rental.md",
                        "exists": True,
                        "content": "# SOP Layanan Rental ISKOM\n1. Ketentuan Sewa Harian & Bulanan\n2. Jaminan KTP Asli Fisik\n3. Toleransi Keterlambatan 2 Jam"
                    },
                    {
                        "name": "products_pricing.json",
                        "path": "knowledge/products_pricing.json",
                        "exists": True,
                        "content": "Katalog Resmi Laptop Rental: ThinkPad T480, Dell Latitude 5490, HP ProBook 440 G5."
                    }
                ]
            })
        return self._json({
            "agents": agent_memories,
            "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def handle_get_folders(self):
        import datetime
        snap = orchestrator.state.snapshot()
        agents = snap["agents"]
        agent_file_map = {
            "AGENT-SLS-01": "agents/sales_agent.py",
            "AGENT-INV-01": "agents/inventory_agent.py",
            "AGENT-FIN-01": "agents/finance_agent.py",
            "AGENT-CS-01": "agents/cs_agent.py",
            "AGENT-KPI-01": "agents/kpi_agent.py",
            "AGENT-MGR-01": "core/orchestrator.py",
            "AGENT-OPS-01": "agents/sales_agent.py",
            "AGENT-MKT-01": "agents/sales_agent.py",
            "AGENT-PRS-01": "agents/sales_agent.py",
            "AGENT-COL-01": "agents/finance_agent.py",
        }
        return self._json({
            "agents": [
                {
                    "profile": a["id"],
                    "label": a["name"],
                    "available": True,
                    "path": agent_file_map.get(a["id"], f"agents/{a['id'].lower().replace('-', '_')}.py")
                } for a in agents
            ],
            "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def handle_get_folder_list(self, profile, sub_path=""):
        import datetime
        snap = orchestrator.state.snapshot()
        agent = next((a for a in snap["agents"] if a["id"] == profile), None)
        agent_name = agent["name"] if agent else profile

        agent_file_map = {
            "AGENT-SLS-01": "agents/sales_agent.py",
            "AGENT-INV-01": "agents/inventory_agent.py",
            "AGENT-FIN-01": "agents/finance_agent.py",
            "AGENT-CS-01": "agents/cs_agent.py",
            "AGENT-KPI-01": "agents/kpi_agent.py",
            "AGENT-MGR-01": "core/orchestrator.py",
            "AGENT-OPS-01": "agents/sales_agent.py",
            "AGENT-MKT-01": "agents/sales_agent.py",
            "AGENT-PRS-01": "agents/sales_agent.py",
            "AGENT-COL-01": "agents/finance_agent.py",
        }
        py_rel = agent_file_map.get(profile, "agents/sales_agent.py")
        py_name = os.path.basename(py_rel)
        py_abs = os.path.join(BASE_DIR, py_rel)
        py_size = os.path.getsize(py_abs) if os.path.isfile(py_abs) else 3800

        sop_abs = os.path.join(BASE_DIR, "knowledge", "sop_rental.md")
        sop_size = os.path.getsize(sop_abs) if os.path.isfile(sop_abs) else 1950

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        entries = [
            {"name": "SOUL.md", "path": "SOUL.md", "type": "file", "size": 420, "modified": now_iso, "sensitive": False},
            {"name": "MEMORY.md", "path": "MEMORY.md", "type": "file", "size": 650, "modified": now_iso, "sensitive": False},
            {"name": "USER.md", "path": "USER.md", "type": "file", "size": 310, "modified": now_iso, "sensitive": False},
            {"name": py_name, "path": py_name, "type": "file", "size": py_size, "modified": now_iso, "sensitive": False},
            {"name": "sop_rental.md", "path": "sop_rental.md", "type": "file", "size": sop_size, "modified": now_iso, "sensitive": False}
        ]
        return self._json({
            "profile": profile,
            "path": sub_path,
            "entries": entries,
            "truncated": False,
            "hiddenCount": 0
        })

    def handle_get_folder_file(self, profile, file_path):
        import datetime
        fname = file_path.split("/")[-1] if "/" in file_path else file_path
        snap = orchestrator.state.snapshot()
        agent = next((a for a in snap["agents"] if a["id"] == profile), None)
        role = agent["role"] if agent else "ISKOM AI Agent"
        name = agent["name"] if agent else profile

        agent_file_map = {
            "AGENT-SLS-01": "agents/sales_agent.py",
            "AGENT-INV-01": "agents/inventory_agent.py",
            "AGENT-FIN-01": "agents/finance_agent.py",
            "AGENT-CS-01": "agents/cs_agent.py",
            "AGENT-KPI-01": "agents/kpi_agent.py",
            "AGENT-MGR-01": "core/orchestrator.py",
            "AGENT-OPS-01": "agents/sales_agent.py",
            "AGENT-MKT-01": "agents/sales_agent.py",
            "AGENT-PRS-01": "agents/sales_agent.py",
            "AGENT-COL-01": "agents/finance_agent.py",
        }

        if fname == "SOUL.md":
            content = (
                f"# SOUL & IDENTITY: {name} ({profile})\n\n"
                f"- **Peran**: {role}\n"
                f"- **Perusahaan**: CV ISKOM (Rental Laptop & IT Hardware)\n"
                f"- **Domain**: Solusi rental B2B & pengadaan perangkat laptop/PC\n"
                f"- **Status Operasional**: Active System Agent di Core Orchestrator\n"
                f"- **Model**: Google Gemini 1.5 Flash\n"
            )
        elif fname == "MEMORY.md":
            content = (
                f"# MEMORY CONTEXT & ATURAN BISNIS: {name}\n\n"
                f"1. **Batas Diskon**: Diskon <= 10% dapat disetujui otomatis. Diskon > 10% WAJIB eskalasi ke Fabian (Direktur).\n"
                f"2. **Pengecekan Stok**: Ketersediaan unit wajib mengacu pada database inventaris fisik terkini.\n"
                f"3. **Keamanan & Guardrails**: Segala permintaan kredensial, SMS OTP, atau CAPTCHA WAJIB diserahkan ke Owner via Intercept Mode.\n"
                f"4. **Nilai Transaksi**: Transaksi sewa >= Rp 25.000.000 memerlukan verifikasi bertingkat.\n"
            )
        elif fname == "USER.md":
            content = (
                "# PROFIL PENGGUNA (OWNER & DIREKTUR)\n\n"
                "- **Nama**: Fabian\n"
                "- **Jabatan**: Direktur Utama CV ISKOM\n"
                "- **Hak Akses**: Superadmin / Approval Authority Level 1\n"
                "- **Delegasi**: Menangani resolusi OTP/CAPTCHA, approval diskon tinggi, dan SPK bernilai besar.\n"
            )
        elif fname == "sop_rental.md":
            sop_path = os.path.join(BASE_DIR, "knowledge", "sop_rental.md")
            if os.path.isfile(sop_path):
                with open(sop_path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = "# SOP RENTAL LAPTOP ISKOM\nSyarat jaminan KTP asli fisik."
        else:
            py_rel = agent_file_map.get(profile, "agents/sales_agent.py")
            py_abs = os.path.join(BASE_DIR, py_rel)
            if not os.path.isfile(py_abs):
                py_abs = os.path.join(BASE_DIR, "agents", fname)
            if os.path.isfile(py_abs):
                with open(py_abs, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = f"# Source code implementation for {name} ({profile})\n# File: {py_rel}"

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return self._json({
            "profile": profile,
            "path": file_path,
            "size": len(content.encode("utf-8")),
            "modified": now_iso,
            "kind": "text",
            "content": content
        })

    def handle_get_knowledge(self):
        import datetime
        return self._json({
            "skills": {
                "availability": "available",
                "data": [
                    {"name": "rental_calculator", "category": "Pricing & Billing", "source": "tools/rental_calculator.py", "trust": "verified", "status": "enabled"},
                    {"name": "inventory_checker", "category": "Warehouse", "source": "tools/inventory_tools.py", "trust": "verified", "status": "enabled"},
                    {"name": "payment_mock", "category": "Finance", "source": "tools/payment_mock.py", "trust": "verified", "status": "enabled"},
                    {"name": "ticket_manager", "category": "Support", "source": "tools/ticket_tools.py", "trust": "verified", "status": "enabled"}
                ]
            },
            "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def handle_get_command_log(self):
        import datetime
        logs = read_logs()[-20:]
        entries = []
        for l in logs:
            entries.append({
                "command": l.get("tools_called", ["orchestration"])[0] if l.get("tools_called") else "router_dispatch",
                "ok": l.get("status") == "SUCCESS",
                "durationMs": 14,
                "at": l.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())
            })
        return self._json({
            "entries": entries,
            "health": {
                "total": len(logs),
                "failed": sum(1 for l in logs if l.get("status") != "SUCCESS"),
                "averageMs": 14
            },
            "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def handle_get_logs(self):
        import datetime
        logs = read_logs()[-40:]
        logs.reverse()
        data_lines = []
        for l in logs:
            ts = l.get("timestamp", "").split("T")[-1][:8] if "T" in l.get("timestamp", "") else "00:00:00"
            agent = l.get("agent_name") or l.get("agent_id") or "SYSTEM"
            inp = l.get("user_input") or "-"
            act = l.get("action") or l.get("keputusan") or l.get("result") or "-"
            status = l.get("status", "SUCCESS")
            lvl = "INFO" if status == "SUCCESS" else ("WARNING" if status == "PENDING_APPROVAL" else "ERROR")
            data_lines.append({
                "text": f"[{ts}] [{lvl}] {agent}: {inp} -> {act}",
                "level": lvl
            })

        return self._json({
            "files": [
                {
                    "name": "activity_logs.jsonl",
                    "label": "ISKOM AI-OS Audit Trail",
                    "source": {
                        "availability": "available",
                        "data": data_lines
                    }
                }
            ],
            "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def handle_get_office(self):
        import datetime
        snap = orchestrator.state.snapshot()
        agents = snap["agents"]
        stations = []
        for idx, a in enumerate(agents):
            status = a.get("status", "IDLE")
            powered = a.get("powered", False)
            if not powered or status == "OFFLINE":
                state = "Offline"
                room = "Lounge"
                room_pos = f"lounge-seat-{(idx % 3) + 1}"
            elif status == "WORKING":
                state = "Working"
                room = "Workspace"
                room_pos = f"seat-{idx + 1}"
            elif status in ("WAITING_APPROVAL", "HUMAN_NEEDED"):
                state = "Reviewing"
                room = "Workspace"
                room_pos = "meeting-area"
            else:
                state = "Idle"
                room = "Lounge"
                room_pos = f"lounge-seat-{(idx % 3) + 1}"

            task_desc = a.get("task") or "Standby / Siaga"
            short_act = (task_desc[:28] + "...") if len(task_desc) > 28 else task_desc
            stations.append({
                "id": a["id"],
                "name": a["short"],
                "role": a["role"],
                "room": room,
                "roomPosition": room_pos,
                "state": state,
                "currentTask": task_desc,
                "recentActivity": a.get("last_reply") or "Belum ada riwayat aktivitas.",
                "activity": short_act if state == "Working" else "",
                "seat": idx + 1,
                "provenance": "ISKOM Core Orchestrator",
                "freshness": "live",
                "privacy": "unlocked"
            })

        summary = {
            "declared": len(agents),
            "active": sum(1 for a in stations if a["state"] == "Working"),
            "idle": sum(1 for a in stations if a["state"] == "Idle"),
            "offline": sum(1 for a in stations if a["state"] == "Offline"),
            "unknown": 0,
            "gatewaysReachable": sum(1 for a in stations if a["state"] != "Offline"),
            "gatewaysDeclared": len(agents)
        }
        return self._json({
            "stations": stations,
            "summary": summary,
            "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def handle_get_activity(self):
        import datetime
        logs = read_logs()[-10:]
        logs.reverse()
        sessions = []
        for idx, l in enumerate(logs):
            sessions.append({
                "id": f"SES-{idx+1:02d}",
                "title": l.get("user_input") or "Perintah Sistem",
                "preview": l.get("action") or l.get("result") or "Selesai",
                "lastActive": l.get("timestamp", "").split("T")[-1][:8] if "T" in l.get("timestamp", "") else "Baru saja",
                "actor": l.get("agent_name") or l.get("agent_id") or "Agent",
                "active": False
            })
        return self._json({
            "sessions": {
                "availability": "available",
                "data": sessions
            },
            "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def handle_get_channels(self):
        import datetime
        return self._json({
            "channels": {
                "availability": "available",
                "data": [
                    {"name": "REST API ISKOM", "status": "Connected"},
                    {"name": "Core Orchestrator", "status": "Connected"},
                    {"name": "WhatsApp Business", "status": "Configured"}
                ]
            },
            "activeSessions": 1,
            "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def handle_get_dashboard(self):
        import datetime
        snap = orchestrator.state.snapshot()
        agents = snap["agents"]
        logs = read_logs()
        total_tx = len(logs)
        return self._json({
            "runtime": {
                "profiles": {"availability": "available", "data": [{"name": a["short"], "model": "ISKOM-v2", "gateway": "Running" if a["powered"] else "Stopped"} for a in agents]},
                "openCode": {"availability": "available", "data": "Ready"},
                "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
            },
            "tasks": {
                "availability": "available",
                "total": total_tx,
                "byStatus": {"done": total_tx, "running": snap["summary"]["working"], "pending": snap["summary"]["pending_approvals"]},
                "assigned": snap["summary"]["online"]
            },
            "calendar": {
                "availability": "available",
                "active": 1,
                "paused": 0,
                "nextRun": datetime.datetime.now(datetime.timezone.utc).isoformat()
            },
            "activity": {"availability": "available", "total": total_tx},
            "knowledge": {"availability": "available", "total": 6, "byCategory": {"SOP": 2, "Product": 4}},
            "channels": {"availability": "available", "total": 3, "connected": 2},
            "office": {
                "declared": len(agents),
                "active": snap["summary"]["working"],
                "idle": snap["summary"]["online"] - snap["summary"]["working"],
                "offline": len(agents) - snap["summary"]["online"],
                "unknown": 0,
                "gatewaysReachable": snap["summary"]["online"],
                "gatewaysDeclared": len(agents)
            },
            "commands": {"total": total_tx, "failed": 0, "averageMs": 14},
            "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def handle_get_usage(self):
        import datetime
        snap = orchestrator.state.snapshot()
        agents = snap["agents"]
        agent_usages = []
        for a in agents:
            done = a.get("tasks_done", 0)
            agent_usages.append({
                "agent": a["id"],
                "availability": "available",
                "usage": {
                    "days": 7,
                    "sessions": max(1, done),
                    "messages": max(1, done * 2),
                    "toolCalls": max(0, done),
                    "inputTokens": done * 450 + 200,
                    "outputTokens": done * 280 + 150,
                    "totalTokens": done * 730 + 350,
                    "costUsd": round(done * 0.002, 4),
                    "models": [{"model": "gemini-1.5-flash", "sessions": max(1, done), "tokens": done * 730 + 350}],
                    "tools": [{"tool": "rental_calculator", "calls": done}],
                    "sources": [{"source": "web_chat", "sessions": max(1, done), "tokens": done * 730 + 350}]
                }
            })
        return self._json({
            "days": 7,
            "agents": agent_usages,
            "totals": {
                "sessions": sum(a["usage"]["sessions"] for a in agent_usages),
                "messages": sum(a["usage"]["messages"] for a in agent_usages),
                "toolCalls": sum(a["usage"]["toolCalls"] for a in agent_usages),
                "inputTokens": sum(a["usage"]["inputTokens"] for a in agent_usages),
                "outputTokens": sum(a["usage"]["outputTokens"] for a in agent_usages),
                "totalTokens": sum(a["usage"]["totalTokens"] for a in agent_usages),
                "costUsd": sum(a["usage"]["costUsd"] for a in agent_usages)
            },
            "models": [{"model": "gemini-1.5-flash", "sessions": 10, "tokens": 5000}],
            "sources": [{"source": "web_chat", "sessions": 10, "tokens": 5000}],
            "tools": [{"tool": "rental_calculator", "calls": 10}],
            "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def handle_get_kpi(self):
        logs = read_logs()
        total = len(logs)
        success = sum(1 for l in logs if l.get("status") == "SUCCESS")
        snap = orchestrator.state.snapshot()["summary"]
        return self._json({
            "total_transactions": total,
            "pending_approvals": snap["pending_approvals"],
            "success_rate": f"{(success / max(1, total)) * 100:.1f}%",
            "active_agents": snap["online"],
            "total_agents": snap["total"],
        })

    # -------------------------------------------------------------------- POST
    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        try:
            data = self._body()
        except Exception:
            return self._json({"error": "Body JSON tidak valid"}, 400)

        try:
            if path == "/api/chat":
                return self.handle_chat(data)
            if path == "/api/approve":
                return self.handle_approve(data)
            if path == "/api/agents/power":
                return self._json(orchestrator.state.set_power(data.get("agent_id", ""), bool(data.get("on"))))
            if path == "/api/agents/resolve":
                orchestrator.state.clear_human_needed(data.get("agent_id", ""))
                return self._json({"status": "SUCCESS"})
            return self._json({"error": "Endpoint tidak ditemukan"}, 404)
        except (KeyError, ValueError) as e:
            return self._json({"error": str(e).strip("'")}, 400)
        except Exception as e:
            return self._json({"error": str(e)}, 500)

    def handle_chat(self, data):
        message = (data.get("message") or "").strip()
        if not message:
            return self._json({"error": "Field 'message' wajib diisi"}, 400)
        resp = loop.run_until_complete(
            orchestrator.handle_request(message, user_id=data.get("user_id", "web_user"))
        )
        return self._json({
            "transaction_id": resp.transaction_id,
            "latency_ms": resp.latency_ms,
            "routing": resp.routing.model_dump(),
            "execution": resp.execution.model_dump(),
        })

    def handle_approve(self, data):
        approval_id = data.get("approval_id", "")
        decision = "APPROVED" if data.get("action", "APPROVED") == "APPROVED" else "REJECTED"
        ticket = orchestrator.state.resolve_approval(approval_id, decision)
        if not ticket:
            return self._json({"error": f"Tiket {approval_id} tidak ditemukan / sudah diputuskan"}, 404)

        orchestrator.logger.log_action(
            user="owner_iskom",
            agent_id="OWNER",
            agent_name="Owner ISKOM",
            user_input=f"Keputusan approval {approval_id}",
            keputusan=f"HUMAN_APPROVAL_DECISION: {decision}",
            tools_called=["manage_approval"],
            action=f"APPROVAL_{decision}",
            result=f"Tiket {approval_id} ({ticket['agent_name']}) {decision} oleh Owner",
        )
        return self._json({"status": "SUCCESS", "approval_id": approval_id, "decision": decision})


def run_server(port=PORT):
    os.chdir(BASE_DIR)
    httpd = HTTPServer(('', port), AIOSRequestHandler)
    print("=" * 70)
    print("🏢 ISKOM AI-OS PIXEL OFFICE & API SERVER RUNNING")
    print(f"📍 Pixel Office : http://localhost:{port}")
    print(f"📍 Klasik       : http://localhost:{port}/classic")
    print("=" * 70)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
        httpd.server_close()


if __name__ == "__main__":
    run_server(int(sys.argv[1]) if len(sys.argv) > 1 else PORT)
