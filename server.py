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
        # Redam log polling agar konsol tidak banjir
        if "/api/agents/state" in (args[0] if args else ""):
            return
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

        if path in ("/", "/index.html", "/office"):
            self.path = "/office.html"
            return super().do_GET()
        if path == "/classic":
            self.path = "/dashboard.html"
            return super().do_GET()
        if path == "/api/agents/state":
            return self._json(orchestrator.state.snapshot())
        if path == "/api/logs":
            recent = read_logs()[-25:]
            recent.reverse()
            return self._json(recent)
        if path == "/api/kpi":
            return self.handle_get_kpi()
        return super().do_GET()

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
            if path == "/api/agents/sleep-all":
                return self._json(orchestrator.state.sleep_all())
            if path == "/api/agents/wake-all":
                return self._json(orchestrator.state.wake_all())
            if path == "/api/agents/toggle-sleep":
                if data.get("agent_id"):
                    return self._json(orchestrator.state.toggle_agent_sleep(data["agent_id"]))
                return self._json(orchestrator.state.toggle_sleep_all())
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
