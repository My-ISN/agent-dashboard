# ISKOM AI Operating System (AI-OS) & Multi-Agent Dashboard
## Powered by Nous Hermes (Reasoning Engine) & OpenCode (Execution Sandbox)

---

## 📌 Pengenalan Proyek
Sistem ini dirancang sebagai **AI Operating System Terpusat** untuk mengotomasi operasional sewa laptop & peralatan IT PT/CV ISKOM secara hulu-ke-hilir (*end-to-end*). Dibangun dengan fondasi **Modular Multi-Agent Architecture**, sistem ini dilengkapi dengan:
1. **Business Rule Engine** (Penegakan aturan mutlak, batas diskon & batas nominal).
2. **Human-in-the-Loop Approval Queue** (Wewenang akhir transaksi di tangan Owner).
3. **Strict RBAC Tool Registry** (Akses database melalui API yang berizin, tanpa SQL liar).
4. **Audit Trail Logger** (Setiap input, routing, eksekusi tool, dan latency tercatat transparan).

---

## 📂 Struktur Direktori

```text
ai-core/
├── PRD.md                             # Product Requirement Document (PRD) Lengkap
├── README.md                          # Panduan & Dokumentasi Ringkas
│
├── docs/                              # Deliverables Fase Analisis & Desain (Minggu 1)
│   ├── ROADMAP_2_WEEKS.md             # Jadwal Rinci Day 1 s/d Day 14
│   ├── ARCHITECTURE_AND_FLOWCHART.md  # Diagram Arsitektur & Sequence Flow (Mermaid)
│   ├── 01_company_process_map.md      # Day 1: Pemetaan Proses Bisnis 8 Divisi ISKOM
│   ├── 02_ai_organization_chart.md    # Day 2: Struktur Organisasi Multi-Agent
│   ├── 03_agent_specifications.md     # Day 3: Spesifikasi Rinci Job Description Agent
│   ├── 04_business_rules.md           # Day 4: Aturan Bisnis & Batas Ambang Diskon
│   ├── 05_permission_approval_matrix.md # Day 5: Matriks Hak Akses & Alur Approval
│   └── 06_database_schema_erd.md      # Day 6: Skema Database & Relasi ke HRIS
│
├── core/                              # Fase Prototype (Minggu 2)
│   ├── orchestrator.py                # Kernel Eksekusi Utama
│   ├── router.py                      # Intent Routing via Hermes LLM
│   ├── rule_engine.py                 # Evaluator Aturan & Diskon
│   └── logger.py                      # Activity & Audit Trail Logger
│
├── agents/                            # Definisi & Prompting Spesialis Agent
│   ├── base_agent.py                  # Abstract Agent Base Class
│   ├── sales_rental_agent.py          # Sales & Rental Specialist
│   ├── inventory_agent.py             # Inventory & Unit Specialist
│   ├── finance_agent.py               # Billing & Payment Specialist
│   └── cs_agent.py                    # Customer Care & FAQ Specialist
│
├── tools/                             # Registry Tool Berizin (API Bridge ke DB HRIS)
│   ├── registry.py                    # Tool Decorator & Permission Guard
│   ├── inventory_tools.py             # Cek stok unit, spesifikasi
│   ├── pricing_tools.py               # Kalkulasi tarif sewa & durasi
│   └── rental_tools.py                # Pembuatan Quotation & SPK
│
├── knowledge/                         # Knowledge Base Dinamis (Markdown & JSON)
│   ├── sop_rental_terms.md            # Syarat Jaminan KTP/Perusahaan
│   ├── laptop_catalog.json            # Katalog tipe unit & spesifikasi
│   └── faq_komplain.md                # Panduan teknis & troubleshooting
│
└── logs/                              # Penyimpanan Audit Log Transaksi
```

---

## 🚀 Alur Eksekusi Instruksi (Core Flow)

```text
USER INPUT ➔ AI CORE ➔ ROUTER (Hermes) ➔ SPECIALIST AGENT ➔ KNOWLEDGE BASE
                   ➔ BUSINESS RULES ➔ [APPROVAL OWNER?] ➔ TOOL EXECUTION (HRIS DB)
                   ➔ AUDIT LOGGER ➔ RESPONSE KE USER
```

---

## 📖 Dokumen Referensi Cepat
- **[PRD Lengkap](file:///c:/server/www/ISKOM/ai-core/PRD.md)**: Gambaran kebutuhan, fitur, dan spesifikasi teknis.
- **[Rencana Kerja 2 Minggu](file:///c:/server/www/ISKOM/ai-core/docs/ROADMAP_2_WEEKS.md)**: Checklist pengerjaan harian Day 1 sampai Day 14.
- **[Diagram Arsitektur & Flowchart](file:///c:/server/www/ISKOM/ai-core/docs/ARCHITECTURE_AND_FLOWCHART.md)**: Diagram Mermaid interaktif lengkap.
- **[Company Process Map](file:///c:/server/www/ISKOM/ai-core/docs/01_company_process_map.md)**: Pemetaan operasional 8 divisi bisnis ISKOM.
- **[AI Organization Chart](file:///c:/server/www/ISKOM/ai-core/docs/02_ai_organization_chart.md)**: Struktur komando multi-agent.
