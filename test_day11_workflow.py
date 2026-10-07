"""
Test Suite Day 11: Workflow Engine & State Machine
Menguji siklus hidup tahapan bisnis (Lead -> Quotation -> Approval -> Won/Lost)
dan penegakan larangan lompatan status tidak sah.
"""

import sys
import asyncio
import json

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from core.workflow_engine import WorkflowEngine, LeadState, InvalidStateTransition
from core.orchestrator import CoreOrchestrator


async def test_workflow_engine():
    print("=" * 80)
    print("[*] PENGUJIAN DAY 11: WORKFLOW ENGINE & STATE MACHINE")
    print("=" * 80)

    engine = WorkflowEngine()

    # 1. Uji Happy Path: New Lead -> Qualified -> Follow Up -> Quotation -> Closing -> Won
    print("\n[STEP 1] Uji Alur Standar Penuh (Happy Path -> WON):")
    wf1 = engine.start_lead_workflow(customer_name="PT Maju Bersama")
    print(f"[-] Status Awal             : {wf1.current_state.value}")
    assert wf1.current_state == LeadState.NEW_LEAD

    wf1.transition_to(LeadState.QUALIFIED, actor="AGENT-SLS-01", notes="Kebutuhan 20 unit laptop diverifikasi")
    print(f"[-] Transisi 1 (Kualifikasi) : {wf1.current_state.value}")

    wf1.transition_to(LeadState.FOLLOW_UP, actor="AGENT-FLP-01", notes="Follow-up ketersediaan PIC pengadaan")
    print(f"[-] Transisi 2 (Follow-up)   : {wf1.current_state.value}")

    wf1.transition_to(LeadState.QUOTATION_SENT, actor="AGENT-SLS-01", notes="Surat penawaran harga terkirim")
    print(f"[-] Transisi 3 (Quotation)   : {wf1.current_state.value}")

    wf1.transition_to(LeadState.CLOSING, actor="AGENT-SLS-01", notes="Klien menyetujui penawaran & tanda tangan SPK")
    print(f"[-] Transisi 4 (Closing)     : {wf1.current_state.value}")

    wf1.transition_to(LeadState.WON, actor="AGENT-FIN-01", notes="DP sewa diterima, unit siap kirim")
    print(f"[-] Status Akhir             : {wf1.current_state.value} (Deal Berhasil Ditutup!)")
    assert wf1.current_state == LeadState.WON
    print(f"    Total Riwayat Transisi: {len(wf1.history)} langkah tercatat rapi.")
    print("[+] Status Step 1: PASS")

    # 2. Uji Alur dengan Negosiasi & Approval Owner
    print("\n[STEP 2] Uji Alur Negosiasi & Approval Owner:")
    wf2 = engine.start_lead_workflow(customer_name="CV Citra Mandiri")
    wf2.transition_to(LeadState.QUALIFIED, actor="AGENT-SLS-01")
    wf2.transition_to(LeadState.QUOTATION_SENT, actor="AGENT-SLS-01")
    wf2.transition_to(LeadState.NEGOTIATION, actor="AGENT-SLS-01", notes="Klien minta diskon 15%")
    wf2.transition_to(LeadState.PENDING_APPROVAL, actor="AGENT-SLS-01", notes="Diskon > 10% dikirim ke Owner")
    print(f"[-] Status Saat Ini: {wf2.current_state.value} (Tertahan di Antrean Owner)")

    # Owner menyetujui
    wf2.transition_to(LeadState.CLOSING, actor="OWNER_HUMAN", notes="Owner klik APPROVE diskon 15%")
    wf2.transition_to(LeadState.WON, actor="AGENT-FIN-01", notes="Kontrak sewa resmi aktif")
    print(f"[-] Status Akhir   : {wf2.current_state.value} (Berhasil lolos lewat Approval Owner)")
    assert wf2.current_state == LeadState.WON
    print("[+] Status Step 2: PASS")

    # 3. Uji Penegakan Guardrail: Cegah Lompatan Status Ilegal
    print("\n[STEP 3] Uji Keamanan Guardrail (Cegah Lompatan Status Ilegal):")
    wf3 = engine.start_lead_workflow(customer_name="Pelanggan Uji")
    try:
        # Mencoba langsung melompat dari NEW_LEAD langsung ke WON tanpa tahap penawaran
        wf3.transition_to(LeadState.WON, actor="ILLEGAL_ACTOR")
        print("[x] FAIL: Sistem membiarkan lompatan ilegal!")
        assert False
    except InvalidStateTransition as e:
        print(f"[-] Percobaan Ilegal: NEW_LEAD -> WON")
        print(f"    Respon Sistem: Berhasil DIBLOKIR! ({e})")
        assert wf3.current_state == LeadState.NEW_LEAD
        print("[+] Status Step 3: PASS (Guardrail alur kerja aktif & menolak kecurangan)")

    # 4. Uji End-to-End Sinkronisasi Workflow pada Orchestrator
    print("\n[STEP 4] Uji Integrasi Workflow pada Orchestrator:")
    orchestrator = CoreOrchestrator()

    res = await orchestrator.handle_request("Saya butuh 15 laptop ThinkPad untuk sewa 1 bulan", user_id="Klien PT Digital")
    print(f"[-] Request Masuk: \"{res.user_input}\"")
    print(f"[-] Status Eksekusi: {res.execution.status}")

    active_wfs = orchestrator.workflows.list_active_workflows()
    print(f"[-] Total Workflow Aktif di Orchestrator: {len(active_wfs)}")
    latest_wf = active_wfs[-1]
    print(f"    Workflow ID: {latest_wf['workflow_id']} | Klien: {latest_wf['customer']} | State: {latest_wf['state']}")
    assert latest_wf["state"] in ["QUOTATION_SENT", "QUALIFIED"]
    print("[+] Status Step 4: PASS (Workflow otomatis terbentuk dan terkelola)")

    print("\n" + "=" * 80)
    print("[=] KESIMPULAN: SELURUH PENGUJIAN WORKFLOW ENGINE DAY 11 BERHASIL 100%")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_workflow_engine())
