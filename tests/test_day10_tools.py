"""
Test Suite Day 10: Tool System & RBAC Guard
Menguji 8 Tools Resmi, Pengecekan Izin Eksekusi (RBAC), dan Integrasi End-to-End.
"""

import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
import sys
import asyncio
import json

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from tools.business_tools import registry
from core.orchestrator import CoreOrchestrator


async def test_tools_system():
    print("=" * 80)
    print("[*] PENGUJIAN DAY 10: TOOL SYSTEM & RBAC PERMISSION GUARD")
    print("=" * 80)

    # 1. Verifikasi Registrasi 8 Tool Resmi
    print("\n[STEP 1] Verifikasi Katalog Tool Registry:")
    all_tools = list(registry.tools.keys())
    print(f"[-] Total Tools Terdaftar: {len(all_tools)}")
    for t_name, t_def in registry.tools.items():
        print(f"    • {t_name:<20} : {t_def.description[:55]}... [Izin: {t_def.allowed_agents}]")

    mandatory_tools = [
        "search_customer", "search_product", "check_inventory", "create_lead",
        "create_quotation", "send_message", "create_ticket", "request_approval"
    ]
    for mt in mandatory_tools:
        assert mt in all_tools, f"Tool wajib '{mt}' harus terdaftar!"
    print("[+] Status Step 1: PASS (Seluruh 8 tool wajib terdaftar lengkap)")

    # 2. Uji RBAC Guard: Penolakan Aksi Tidak Berizin
    print("\n[STEP 2] Uji Keamanan RBAC Guard (Pencegahan Aksi Liar):")

    # Uji 2.1: CS Agent mencoba menerbitkan Quotation (Harus DITOLAK)
    illegal_res = await registry.execute(
        "create_quotation",
        caller_agent_id="AGENT-CS-01",
        customer_name="Budi",
        unit_model="ThinkPad",
        qty=5,
        duration_months=1
    )
    print(f"[-] CS Agent memanggil 'create_quotation' -> Status: {illegal_res.get('status')}")
    print(f"    Pesan Penolakan: \"{illegal_res.get('message')}\"")
    assert illegal_res.get("status") == "PERMISSION_DENIED", "Aksi tidak berizin wajib ditolak oleh RBAC Guard!"

    # Uji 2.2: Sales Agent mencoba membuka Tiket Komplain (Harus DITOLAK)
    illegal_res2 = await registry.execute(
        "create_ticket",
        caller_agent_id="AGENT-SLS-01",
        customer_name="Budi",
        issue_category="HARDWARE",
        description="Layar pecah"
    )
    print(f"[-] Sales Agent memanggil 'create_ticket' -> Status: {illegal_res2.get('status')}")
    assert illegal_res2.get("status") == "PERMISSION_DENIED"
    print("[+] Status Step 2: PASS (RBAC Guard sukses menolak pemanggilan tanpa izin)")

    # 3. Uji Eksekusi Tool Berizin
    print("\n[STEP 3] Uji Eksekusi Tool oleh Agen yang Berwenang:")

    # 3.1 Cek Inventaris oleh Inventory Agent
    inv_res = await registry.execute("check_inventory", "AGENT-INV-01", model_or_sku="ThinkPad T480", requested_qty=10)
    print(f"[-] Inventory Agent memanggil 'check_inventory' -> Hasil: {inv_res['result']['message']}")
    assert inv_res["status"] == "SUCCESS"

    # 3.2 Cari Pelanggan oleh CS Agent
    cust_res = await registry.execute("search_customer", "AGENT-CS-01", query="Budi")
    print(f"[-] CS Agent memanggil 'search_customer' -> Ditemukan: {cust_res['result']['customer']['name']}")
    assert cust_res["status"] == "SUCCESS"

    # 3.3 Buat Tiket Komplain oleh CS Agent
    tck_res = await registry.execute(
        "create_ticket",
        "AGENT-CS-01",
        customer_name="Budi Santoso",
        issue_category="HARDWARE",
        description="Keyboard tidak merespons",
        priority="HIGH"
    )
    print(f"[-] CS Agent memanggil 'create_ticket' -> Nomor Tiket: {tck_res['result']['ticket_id']}")
    assert tck_res["status"] == "SUCCESS"

    # 3.4 Kirim Permintaan Approval oleh Sales Agent
    apv_res = await registry.execute(
        "request_approval",
        "AGENT-SLS-01",
        requester_agent_id="AGENT-SLS-01",
        rule_id="RULE-DISC-02",
        category="DISCOUNT_REQUEST",
        payload={"discount": 20.0, "qty": 15},
        rationale="Order sewa proyek 15 unit laptop"
    )
    print(f"[-] Sales Agent memanggil 'request_approval' -> ID Approval: {apv_res['result']['approval_id']}")
    assert apv_res["status"] == "SUCCESS"
    print("[+] Status Step 3: PASS (Eksekusi fungsi tool berhasil dengan validasi izin)")

    # 4. Uji End-to-End Orchestrator Memanggil Tool Resmi
    print("\n[STEP 4] Uji End-to-End Integrasi Orchestrator & Tool Registry:")
    orchestrator = CoreOrchestrator()

    # Skenario A: Order Normal (Menerbitkan Quotation resmi via Tool)
    res_normal = await orchestrator.handle_request("Saya butuh 10 unit ThinkPad T480 untuk sewa kantor")
    print(f"[-] Order Normal -> Tools Dipanggil: {res_normal.execution.tools_called}")
    print(f"    Respon:\n{res_normal.execution.reply_message}\n")
    assert "create_quotation" in res_normal.execution.tools_called

    # Skenario B: Permintaan Diskon 25% (Memicu Tool request_approval)
    res_discount = await orchestrator.handle_request("Saya mau sewa 10 unit ThinkPad T480 tapi minta diskon 25%")
    print(f"[-] Order Diskon 25% -> Tools Dipanggil: {res_discount.execution.tools_called}")
    print(f"    Status: {res_discount.execution.status}")
    print(f"    Respon:\n{res_discount.execution.reply_message}")
    assert "request_approval" in res_discount.execution.tools_called
    assert res_discount.execution.status == "PENDING_APPROVAL"
    print("[+] Status Step 4: PASS (Orchestrator dan Agen memanggil tools sesuai aturan bisnis)")

    print("\n" + "=" * 80)
    print("[=] KESIMPULAN: SELURUH PENGUJIAN TOOL SYSTEM DAY 10 BERHASIL 100%")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_tools_system())
