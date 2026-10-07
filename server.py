"""
ISKOM AI OPERATING SYSTEM — LOCAL WEB SERVER & REST API (DAY 14)
================================================================
Menyajikan Virtual Office Dashboard & REST API untuk interaksi nyata dengan CoreOrchestrator.
Port Default: 8080 (http://localhost:8080)
"""

import os
import sys
import json
import asyncio
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

# Pastikan UTF-8 di Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from core.orchestrator import CoreOrchestrator

# Inisialisasi Orchestrator Global
orchestrator = CoreOrchestrator()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "logs", "activity_logs.jsonl")


class AIOSRequestHandler(SimpleHTTPRequestHandler):
    """Handler HTTP yang melayani static file dan REST API AI-OS"""

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/", "/index.html"]:
            self.path = "/dashboard.html"
            return super().do_GET()

        elif path == "/api/logs":
            self.handle_get_logs()
        elif path == "/api/kpi":
            self.handle_get_kpi()
        else:
            return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/chat":
            self.handle_post_chat()
        elif path == "/api/approve":
            self.handle_post_approve()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_get_logs(self):
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
        
        # Kirim 25 log terakhir
        recent_logs = logs[-25:]
        recent_logs.reverse()

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(recent_logs, ensure_ascii=False).encode("utf-8"))

    def handle_get_kpi(self):
        total_tx = 0
        pending_apv = 0
        success_tx = 0

        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        total_tx += 1
                        try:
                            data = json.loads(line)
                            if data.get("status") == "PENDING_APPROVAL":
                                pending_apv += 1
                            elif data.get("status") == "SUCCESS":
                                success_tx += 1
                        except Exception:
                            pass

        kpi_data = {
            "total_transactions": total_tx,
            "active_rentals": 142,
            "unit_utilization_rate": "87.5%",
            "pending_approvals": pending_apv,
            "success_rate": f"{(success_tx / max(1, total_tx)) * 100:.1f}%",
            "active_agents": 5
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(kpi_data, ensure_ascii=False).encode("utf-8"))

    def handle_post_chat(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        try:
            req_data = json.loads(body)
            message = req_data.get("message", "").strip()
            user_id = req_data.get("user_id", "web_user")

            if not message:
                self.send_error(400, "Field 'message' wajib diisi")
                return

            # Jalankan coroutine orchestrator
            future = orchestrator.handle_request(message, user_id=user_id)
            core_resp = loop.run_until_complete(future)

            res_payload = {
                "transaction_id": core_resp.transaction_id,
                "latency_ms": core_resp.latency_ms,
                "routing": {
                    "agent_id": core_resp.routing.agent_id,
                    "agent_name": core_resp.routing.agent_name,
                    "intent": core_resp.routing.intent,
                    "confidence": core_resp.routing.confidence,
                    "extracted_entities": core_resp.routing.extracted_entities,
                    "reasoning": core_resp.routing.reasoning
                },
                "execution": {
                    "agent_id": core_resp.execution.agent_id,
                    "action_taken": core_resp.execution.action_taken,
                    "reply_message": core_resp.execution.reply_message,
                    "status": core_resp.execution.status,
                    "tools_called": core_resp.execution.tools_called,
                    "requires_approval": core_resp.execution.requires_approval,
                    "approval_details": core_resp.execution.approval_details
                }
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(res_payload, ensure_ascii=False).encode("utf-8"))

        except Exception as e:
            err_payload = {"error": str(e)}
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(err_payload).encode("utf-8"))

    def handle_post_approve(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8")
        try:
            req_data = json.loads(body)
            approval_id = req_data.get("approval_id")
            action = req_data.get("action", "APPROVED")  # APPROVED or REJECTED

            # Log keputusan approval ke logger
            orchestrator.logger.log_event(
                agent_id="SUPER_ADMIN",
                user_id="owner_iskom",
                intent="HUMAN_APPROVAL_DECISION",
                input_text=f"Decision for {approval_id}: {action}",
                tools_called=["manage_approval"],
                status="SUCCESS",
                response_text=f"Tiket {approval_id} telah {action} oleh Owner",
                latency_ms=10
            )

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "SUCCESS", "approval_id": approval_id, "decision": action}).encode("utf-8"))
        except Exception as e:
            self.send_error(500, str(e))


def run_server(port=PORT):
    os.chdir(BASE_DIR)
    server_address = ('', port)
    httpd = HTTPServer(server_address, AIOSRequestHandler)
    print("=" * 70)
    print(f"🚀 ISKOM AI-OS DASHBOARD & API SERVER RUNNING")
    print(f"📍 URL: http://localhost:{port}")
    print(f"📡 API Endpoints:")
    print(f"   - GET  /api/logs  (Fetch live JSONL audit logs)")
    print(f"   - GET  /api/kpi   (Fetch live KPIs)")
    print(f"   - POST /api/chat  (Send prompt to Multi-Agent Orchestrator)")
    print(f"   - POST /api/approve (Approve/Reject pending tickets)")
    print("=" * 70)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
        httpd.server_close()


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(port_arg)
