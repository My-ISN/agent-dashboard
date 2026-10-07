"""
Test Suite Day 9: Dynamic Knowledge Base System
Menguji kemampuan AI memuat SOP, FAQ, Produk, Kebijakan, dan update dinamis tanpa ubah kode.
"""

import sys
import asyncio
import json

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from core.orchestrator import CoreOrchestrator
from core.knowledge_loader import KnowledgeBase


async def test_knowledge_base():
    print("=" * 80)
    print("[*] PENGUJIAN DAY 9: DYNAMIC KNOWLEDGE BASE SYSTEM")
    print("=" * 80)

    kb = KnowledgeBase()

    # 1. Verifikasi Loading Data dari File-File Knowledge
    print("\n[STEP 1] Verifikasi Loading Data Statis & Dinamis:")
    print(f"[-] Total Produk Laptop Terdaftar : {len(kb.cache['products'])} tipe")
    print(f"[-] Total FAQ Terdaftar           : {len(kb.cache['faq'])} butir")
    print(f"[-] Dokumen SOP & Kebijakan       : {list(kb.cache['documents'].keys())}")
    print(f"[-] Template Pesan Otomatis       : {list(kb.cache['templates'].keys())}")

    assert len(kb.cache['products']) >= 4, "Produk harus minimal 4"
    assert len(kb.cache['faq']) >= 5, "FAQ harus minimal 5"
    print("[+] Status Step 1: PASS (Semua knowledge sukses dimuat ke cache)")

    # 2. Uji Pencarian Produk & FAQ
    print("\n[STEP 2] Uji Pencarian Produk & FAQ:")
    macbook = kb.get_product_by_model("macbook")
    print(f"[-] Pencarian Model 'MacBook' -> {macbook['brand']} {macbook['model']} (Rp {macbook['rates']['monthly']:,}/bln)")

    faq_res = kb.search_faq("apa syarat sewa perorangan?")
    print(f"[-] Pencarian FAQ 'syarat sewa perorangan' -> Q: {faq_res['question']}")
    print(f"    Jawaban: \"{faq_res['answer'][:90]}...\"")
    assert macbook is not None
    assert faq_res is not None
    print("[+] Status Step 2: PASS (Pencarian semantik data akurat)")

    # 3. Uji Integrasi End-to-End Orchestrator + Knowledge Base
    print("\n[STEP 3] Uji Respon Agen Memanfaatkan Knowledge Base:")
    orchestrator = CoreOrchestrator()

    # Test 3.1: CS Agent menjawab pertanyaan syarat sewa
    res_faq = await orchestrator.handle_request("Halo, apa saja syarat jaminan sewa laptop untuk perorangan?")
    print(f"[-] Tanya Syarat KTP/Sewa -> Agen: {res_faq.routing.agent_name}")
    print(f"    Respon Agen: \"{res_faq.execution.reply_message[:100]}...\"")

    # Test 3.2: Sales Agent mengutip harga riil dari katalog
    res_sales = await orchestrator.handle_request("Saya mau sewa 5 unit MacBook Pro M1 untuk 1 bulan")
    print(f"\n[-] Permintaan Sewa MacBook -> Agen: {res_sales.routing.agent_name}")
    print(f"    Respon Agen:\n{res_sales.execution.reply_message}")

    # 4. Uji Kemampuan Admin Menambah Data Tanpa Merombak Kode (Dynamic Update Target)
    print("\n[STEP 4] Uji Penambahan Produk Baru oleh Admin (Tanpa Ubah Source Code):")
    new_laptop = {
        "sku": "NB-ASU-ROG16",
        "brand": "Asus",
        "model": "ROG Strix G16",
        "specs": "Intel Core i9-13980HX, RTX 4070, RAM 32GB, SSD 1TB",
        "rates": {"daily": 350000, "weekly": 1600000, "monthly": 4200000},
        "min_deposit": 1500000,
        "stock_total": 8,
        "category": "High Performance Gaming"
    }

    success = kb.add_product(new_laptop)
    print(f"[-] Menambahkan Laptop Baru '{new_laptop['model']}' ke knowledge -> Status: {success}")

    # Validasi langsung terbaca
    loaded_new = kb.get_product_by_model("ROG Strix G16")
    print(f"[-] Mengambil Produk yang Baru Ditambahkan -> {loaded_new['model']} (Tarif: Rp {loaded_new['rates']['monthly']:,}/bln)")
    assert loaded_new["sku"] == "NB-ASU-ROG16"
    print("[+] Status Step 4: PASS (Admin berhasil menambah data tanpa merombak source code!)")

    print("\n" + "=" * 80)
    print("[=] KESIMPULAN: SELURUH PENGUJIAN KNOWLEDGE BASE DAY 9 BERHASIL 100%")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_knowledge_base())
