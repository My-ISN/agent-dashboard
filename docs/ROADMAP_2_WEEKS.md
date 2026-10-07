# RENCANA KERJA 2 MINGGU (2-WEEK ROADMAP)
## Proyek: AI Operating System & Multi-Agent Dashboard (Hermes & OpenCode)

---

## 🎯 Target Utama & Prinsip Kerja
- **Tujuan**: Membangun Core AI Operating System yang terintegrasi, modular, terukur, memiliki batas kewenangan jelas (*Permission & Approval Matrix*), dan anti-halusinasi.
- **Filosofi**: *Architecture first, code second*. Jangan menulis ribuan baris kode sebelum struktur fondasi, aturan bisnis, dan relasi data tervalidasi.

---

## 📅 MINGGU 1: ANALISIS & DESAIN CORE

| Hari | Target / Milestone | Fokus Pengerjaan | Output / Deliverable |
| :--- | :--- | :--- | :--- |
| **DAY 1** | **Mapping Perusahaan** | Memetakan seluruh divisi bisnis rental laptop ISKOM (Marketing, Sales, CS, Rental Ops, Inventory, Finance, HR, Management). Identifikasi input, output, tools, approval, dan bottleneck. | `01_company_process_map.md` |
| **DAY 2** | **Desain Struktur AI Organization** | Merancang hirarki organisasi AI dari *AI Business Manager* hingga agent spesialis (*Sales Agent*, *Inventory Agent*, dll). | `02_ai_organization_chart.md` |
| **DAY 3** | **Agent Job Description & Spec** | Menetapkan template standar spesifikasi agent (Tujuan, Tugas, Input, Output, Knowledge, Tools, Batas Kewenangan, KPI, Eskalasi). | `03_agent_specifications.md` |
| **DAY 4** | **Business Rule Engine** | Menentukan aturan bisnis deterministik (Diskon $\le 10\%$, Transaksi Besar, Refund, Anti-Halusinasi, OTP/CAPTCHA human fallback). | `04_business_rules.md` |
| **DAY 5** | **Permission Matrix & Approval Flow** | Merancang matriks hak akses agen (Read, Write, Execute, Need_Approval) dan diagram alur *Human-in-the-Loop* ke Owner. | `05_permission_approval_matrix.md` |
| **DAY 6** | **Database Design & ERD** | Merancang skema tabel database untuk AI Core (`agents`, `tools`, `rules`, `approvals`, `logs`, `knowledge`) & relasi ke DB HRIS. | `06_database_schema_erd.md` |
| **DAY 7** | **Review Minggu 1** | Presentasi komprehensif 6 pilar desain kepada Owner sebelum memulai fase coding. | Presentasi & Approval Desain |

---

## 📅 MINGGU 2: MEMBUAT CORE PROTOTYPE

| Hari | Target / Milestone | Fokus Pengerjaan | Output / Deliverable |
| :--- | :--- | :--- | :--- |
| **DAY 8** | **AI Core Architecture & Router** | Mengembangkan kernel orchestrator menggunakan Hermes LLM untuk klasifikasi intent dan routing permintaan pengguna ke agent yang tepat. | `core/router.py` & `core/orchestrator.py` |
| **DAY 9** | **Knowledge Base Engine** | Membangun repositori data dinamis (SOP sewa, pricelist laptop, syarat jaminan KTP/PT, FAQ) yang dapat di-update tanpa redeploy. | `knowledge/` & `core/knowledge_loader.py` |
| **DAY 10** | **Tool Registry & RBAC Guard** | Membangun registry fungsi/alat (`check_inventory`, `calculate_price`, `create_quotation`) yang memiliki validasi izin ketat. | `tools/registry.py` & `tools/rental_tools.py` |
| **DAY 11** | **Workflow Engine** | Mengimplementasikan state machine untuk siklus bisnis: *New Lead $\rightarrow$ Qualification $\rightarrow$ Follow-up $\rightarrow$ Quotation $\rightarrow$ Approval $\rightarrow$ Won*. | `core/workflow_engine.py` |
| **DAY 12** | **Logging & Monitoring Dashboard** | Mencatat setiap aktivitas agen ke dalam log terstruktur (waktu, user, agent, tool, latency, token, approval status) dan visualisasinya. | `core/logger.py` & `dashboard/` |
| **DAY 13** | **Testing Core (20+ Skenario Nyata)** | Uji ketahanan sistem: pencarian produk, kalkulasi sewa, penolakan diskon melebihi wewenang, penanganan data tidak ditemukan, dan fallback OTP. | `tests/test_scenarios.py` & Test Report |
| **DAY 14** | **Demo, Evaluasi & Roadmap Lanjutan** | Presentasi prototype live di depan atasan: simulasi percakapan end-to-end dengan verifikasi approval Owner secara real-time. | Live Demo & Dokumentasi Akhir |

---

## 🏆 8 DELIVERABLES UTAMA DI AKHIR MINGGU 2

1. **AI Organization Chart** : Peta hirarki dan rantai komando seluruh agen.
2. **Company Process Map** : Peta alur proses bisnis sewa & operasional perusahaan.
3. **Agent Registry & Specifications** : Katalog spesifikasi detail seluruh agen.
4. **Business Rule Engine** : Kumpulan aturan mutlak yang membatasi tindakan agen.
5. **Permission & Approval Matrix** : Tabel hak akses dan prosedur persetujuan Owner.
6. **Database Architecture & ERD** : Struktur penyimpanan data dan relasi ke HRIS.
7. **AI Core Prototype** : Kernel sistem fungsional (Router $\rightarrow$ Agent $\rightarrow$ Tool $\rightarrow$ Rule $\rightarrow$ Result).
8. **Technical Documentation** : Panduan implementasi & petunjuk onboarding developer berikutnya.
