"""
Test Suite Day 12: Activity Logging & Monitoring Dashboard
Menguji pencatatan 10 parameter audit trail, persistensi file JSONL, dan metrik monitoring.
"""

import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
import sys
import asyncio
import os
import json

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from core.logger import ActivityLogger
from core.orchestrator import CoreOrchestrator


async def test_logging_and_monitoring():
    print("=" * 80)
    print("[*] PENGUJIAN DAY 12: ACTIVITY AUDIT LOGGING & MONITORING")
    print("=" * 80)

    logger = ActivityLogger()

    # 1. Uji Pencatatan Log Manual dengan 10 Parameter Wajib
    print("\n[STEP 1] Uji Struktur 10 Parameter Audit Trail:")
    log_entry = logger.log_action(
        user="cust_pt_sinergi",
        agent_id="AGENT-SLS-01",
        agent_name="Sales & Rental Agent",
        user_input="Sewa 20 laptop ThinkPad T480",
        keputusan="RENTAL_SALES_INQUIRY (92%)",
        tools_called=["check_inventory", "create_quotation"],
        action="QUOTATION_ISSUED",
        result="Quotation resmi #QUO/2026/01 berhasil diterbitkan",
        error=None,
        approval_required=False,
        latency_ms=3
    )

    # Validasi 10 atribut wajib dari instruksi atasan
    mandatory_fields = ["waktu", "user", "agent", "input", "keputusan", "tool", "action", "result", "error", "approval"]
    for field in mandatory_fields:
        assert field in log_entry, f"Parameter wajib '{field}' hilang dari log entry!"
        print(f"    ✓ Field '{field:<10}' : {log_entry[field]}")

    print("[+] Status Step 1: PASS (Semua 10 parameter wajib tercatat sempurna)")

    # 2. Uji Persistensi File Log JSONL
    print("\n[STEP 2] Verifikasi Penyimpanan File JSONL di Disk:")
    assert os.path.exists(logger.log_file), f"File log '{logger.log_file}' harus ada!"
    with open(logger.log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"[-] Lokasi File Log: {logger.log_file}")
    print(f"[-] Total Baris Log di Disk: {len(lines)} baris")
    assert len(lines) >= 1
    print("[+] Status Step 2: PASS (Data log tersimpan permanen di disk)")

    # 3. Uji End-to-End Orchestrator Logging Otomatis
    print("\n[STEP 3] Uji Otomatisasi Logging pada Orchestrator:")
    orchestrator = CoreOrchestrator()

    # Eksekusi aksi normal
    await orchestrator.handle_request("Saya mau sewa 5 laptop ThinkPad", user_id="user_test_1")
    # Eksekusi aksi yang butuh approval
    await orchestrator.handle_request("Sewa 10 laptop tapi minta diskon 25%", user_id="user_test_2")

    metrics = orchestrator.logger.get_metrics_summary()
    print(f"[-] Total Request Tercatat : {metrics['total_requests']}")
    print(f"[-] Tingkat Keberhasilan   : {metrics['success_rate']}%")
    print(f"[-] Pending Approval Owner : {metrics['pending_approvals']} antrean")
    print(f"[-] Rata-rata Latency      : {metrics['avg_latency_ms']} ms")
    print(f"[-] Distribusi Agen        : {metrics['agent_distribution']}")

    assert metrics["total_requests"] >= 2
    assert metrics["pending_approvals"] >= 1
    print("[+] Status Step 3: PASS (Orchestrator mencatat aktivitas & metrik secara otomatis)")

    # 4. Verifikasi Tampilan Visual Dashboard HTML
    print("\n[STEP 4] Verifikasi File Visual Monitoring Dashboard HTML:")
    dashboard_path = os.path.join(ROOT_DIR, "dashboard.html")
    assert os.path.exists(dashboard_path), f"File 'dashboard.html' harus ada di {dashboard_path}!"
    size_bytes = os.path.getsize(dashboard_path)
    print(f"[-] File Dashboard HTML: {dashboard_path} ({size_bytes:,} bytes)")
    print("[+] Status Step 4: PASS (Virtual Office 2D & Monitoring Dashboard siap dibuka)")

    print("\n" + "=" * 80)
    print("[=] KESIMPULAN: SELURUH PENGUJIAN LOGGING & MONITORING DAY 12 BERHASIL 100%")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_logging_and_monitoring())
