"""
Test Suite Day 8: AI Core Architecture & Semantic Router
Menguji keakuratan klasifikasi intent dan routing instruksi ke agen spesialis.
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

from core.orchestrator import CoreOrchestrator


TEST_SCENARIOS = [
    {
        "prompt": "Saya butuh 50 laptop untuk training kantor selama 1 bulan",
        "expected_agent": "AGENT-SLS-01",
        "expected_intent": "RENTAL_SALES_INQUIRY"
    },
    {
        "prompt": "Apakah ada stok Lenovo ThinkPad Core i5 ready 10 unit di gudang besok?",
        "expected_agent": "AGENT-INV-01",
        "expected_intent": "INVENTORY_STOCK_CHECK"
    },
    {
        "prompt": "Tolong cek invoice #INV-2026-081 apakah sudah lunas atau belum",
        "expected_agent": "AGENT-FIN-01",
        "expected_intent": "FINANCE_BILLING_QUERY"
    },
    {
        "prompt": "Laptop yang kemarin disewa layarnya bergaris dan mati, tolong diganti unitnya",
        "expected_agent": "AGENT-CS-01",
        "expected_intent": "TECHNICAL_SUPPORT_COMPLAINT"
    },
    {
        "prompt": "Berapa total omset sewa laptop dan tingkat utilisasi unit bulan ini untuk laporan?",
        "expected_agent": "AGENT-KPI-01",
        "expected_intent": "EXECUTIVE_KPI_QUERY"
    },
    {
        "prompt": "Mau sewa 15 laptop Dell, tapi tolong kasih diskon 20% ya",
        "expected_agent": "AGENT-SLS-01",
        "expected_intent": "RENTAL_SALES_INQUIRY"
    }
]


async def run_tests():
    print("=" * 80)
    print("[*] PENGUJIAN DAY 8: AI CORE ARCHITECTURE & ROUTER EVALUATION")
    print("=" * 80)

    orchestrator = CoreOrchestrator()
    passed = 0

    for idx, test in enumerate(TEST_SCENARIOS, 1):
        prompt = test["prompt"]
        print(f"\n[TEST CASE #{idx}]")
        print(f"[-] Input User  : \"{prompt}\"")
        
        response = await orchestrator.handle_request(prompt)
        routing = response.routing
        exec_res = response.execution

        print(f"[>] Routed Agent: {routing.agent_id} ({routing.agent_name})")
        print(f"[>] Intent       : {routing.intent} (Confidence: {routing.confidence * 100:.1f}%)")
        print(f"[>] Entities     : {json.dumps(routing.extracted_entities)}")
        print(f"[>] Latency      : {response.latency_ms} ms")
        print(f"[>] Status       : {exec_res.status} (Action: {exec_res.action_taken})")
        print(f"[>] Respon Agent : \"{exec_res.reply_message[:90]}...\"")

        is_match = (routing.agent_id == test["expected_agent"])
        if is_match:
            print(f"[+] HASIL        : PASS (Sesuai Target)")
            passed += 1
        else:
            print(f"[x] HASIL        : FAIL (Target: {test['expected_agent']}, Aktual: {routing.agent_id})")

    print("\n" + "=" * 80)
    print(f"[=] SUMMARY: {passed}/{len(TEST_SCENARIOS)} Test Cases Berhasil ({(passed/len(TEST_SCENARIOS))*100:.1f}%)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_tests())
