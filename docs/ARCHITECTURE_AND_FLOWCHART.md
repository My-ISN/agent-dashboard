# ARSITEKTUR SISTEM & DIAGRAM ALUR (FLOWCHART MERMAID)
## ISKOM AI Operating System & Multi-Agent Dashboard

Dokumen ini memuat representasi visual arsitektur perangkat lunak, siklus hidup eksekusi instruksi, rantai *Human-in-the-Loop Approval*, dan *State Machine Workflow*.

---

## 1. Arsitektur Tingkat Tinggi (High-Level Architecture)

```mermaid
graph TB
    subgraph Client_Layer["1. Client & Interface Layer"]
        StaffWeb["Web Dashboard (Staff / CS / Sales)"]
        OwnerMobile["Owner Approval UI (Web / Mobile)"]
        CustomerChat["WhatsApp / Web Rental Form"]
    end

    subgraph Core_Layer["2. AI-OS Core Kernel (Hermes Engine)"]
        Gateway["API Gateway & Session Manager"]
        Router["Intent Classifier & Semantic Router"]
        Orchestrator["Agent Orchestration Engine"]
        ContextMgr["Conversation State & Context Manager"]
    end

    subgraph Agent_Layer["3. Specialized Agent Layer"]
        MgrAgent["AI Business Manager"]
        SalesAgent["Sales & Rental Agent"]
        InvAgent["Inventory & Unit Agent"]
        FinAgent["Finance & Billing Agent"]
        CSAgent["Customer Service Agent"]
        KPIAgent["Executive & KPI Agent"]
    end

    subgraph Security_Layer["4. Guardrails & Governance"]
        RuleEngine["Business Rule Engine (Diskon, Limit, Threshold)"]
        PermEngine["Permission Matrix (RBAC Guard)"]
        ApprovalQueue["Human-in-the-Loop Approval Queue"]
    end

    subgraph Execution_Layer["5. Execution & Tools"]
        OpenCode["OpenCode Sandbox (Kalkulator & Analisis Data)"]
        ToolReg["Tool Registry API Gateway"]
    end

    subgraph Storage_Layer["6. Data & Knowledge Base"]
        KnowledgeBase[("Knowledge Base (Markdown / Vector Store)")]
        HRIS_DB[("HRIS MySQL Database (Rental, Invoices, Units)")]
        AuditDB[("Activity & Audit Log Database")]
    end

    Client_Layer --> Gateway
    Gateway --> Router
    Router --> Orchestrator
    Orchestrator <--> ContextMgr

    Orchestrator --> MgrAgent
    MgrAgent --> SalesAgent & InvAgent & FinAgent & CSAgent & KPIAgent

    SalesAgent & InvAgent & FinAgent & CSAgent & KPIAgent --> RuleEngine
    RuleEngine --> PermEngine
    
    PermEngine -->|Melebihi Kuota / Perlu Izin| ApprovalQueue
    ApprovalQueue <-->|Notifikasi & Keputusan| OwnerMobile
    
    PermEngine -->|Lolos Validasi| ToolReg
    ToolReg --> OpenCode
    ToolReg --> HRIS_DB
    ToolReg --> KnowledgeBase
    ToolReg --> AuditDB
```

---

## 2. Diagram Urutan Eksekusi (Sequence Diagram: Request to Result)

Diagram ini mengilustrasikan alur pemrosesan saat pengguna meminta penawaran harga dengan permintaan diskon khusus:

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Customer
    participant Core as AI Core Orchestrator
    participant Router as Intent Router (Hermes)
    participant Agent as Sales Agent
    participant Rule as Business Rule Engine
    actor Owner as Owner (Human Approver)
    participant Tool as Tool Registry
    participant DB as HRIS Database
    participant Log as Audit Logger

    User->>Core: "Saya mau sewa 25 Laptop Lenovo i5 selama 1 bulan, minta diskon 15%"
    Core->>Router: Parse intent & entities
    Router-->>Core: Route to Sales Agent (Confidence 98%)
    
    Core->>Agent: Delegasikan permintaan
    Agent->>Tool: check_inventory(specs="Lenovo i5", qty=25, duration="1 month")
    Tool->>DB: Query stok unit tersedia
    DB-->>Tool: Stok 30 unit tersedia (Aman)
    Tool-->>Agent: Ketersediaan terkonfirmasi
    
    Agent->>Tool: calculate_rental_price(unit=25, price_normal=12500000)
    Tool-->>Agent: Total normal = Rp 12.500.000, Diskon 15% = Rp 1.875.000
    
    Agent->>Rule: Validasi aturan: Diskon 15% (Threshold maks agen = 10%)
    Rule-->>Agent: Rule Violation: Butuh Approval Owner!
    
    Agent->>Core: Request Pending Approval
    Core->>Log: Catat status: PENDING_APPROVAL
    Core->>Owner: Push Notifikasi: "Permintaan Diskon 15% untuk 25 Laptop (Rp 10.625.000)"
    Core-->>User: "Permintaan sewa Anda memenuhi syarat. Diskon 15% sedang menunggu verifikasi Owner (estimasi < 5 menit)."
    
    Note over Owner: Owner membuka Dashboard & klik APPROVE
    Owner->>Core: Submit Decision: APPROVED
    
    Core->>Agent: Lanjutkan eksekusi
    Agent->>Tool: create_rental_quotation(customer_id, items, discount=15%)
    Tool->>DB: Insert record quotation resmi
    DB-->>Tool: Quotation ID: #QUO-2026-0881
    
    Tool->>Log: Catat transaksi sukses & approved
    Agent-->>Core: Quotation siap kirim
    Core-->>User: "Penawaran diskon 15% telah disetujui! Nomor Quotation: #QUO-2026-0881."
```

---

## 3. Diagram Status Persetujuan (Approval State Machine)

Setiap aksi transaksi yang memerlukan campur tangan manusia (*Human-in-the-Loop*) melewati state machine berikut:

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Agent merancang tindakan (Action Proposal)
    
    DRAFT --> EVALUATING_RULE : Kirim ke Business Rule Engine
    
    EVALUATING_RULE --> AUTO_APPROVED : Diskon <= 10% & Nilai < Batas Ambang
    EVALUATING_RULE --> REQUIRE_APPROVAL : Diskon > 10% ATAU Nilai Transaksi Besar ATAU Refund
    
    REQUIRE_APPROVAL --> PENDING_OWNER : Push ke Antrean Dashboard Owner
    
    PENDING_OWNER --> APPROVED : Owner klik Setujui
    PENDING_OWNER --> REJECTED : Owner klik Tolak / Beri Catatan
    PENDING_OWNER --> EXPIRED : Timeout (> 24 Jam Tanpa Respon)
    
    AUTO_APPROVED --> EXECUTING_TOOL : Panggil Tool Registry
    APPROVED --> EXECUTING_TOOL : Panggil Tool Registry
    
    REJECTED --> NOTIFIED_USER : Informasikan Penolakan Sopan & Alternatif
    EXPIRED --> ESCALATED_HUMAN : Alihkan ke Staf Sales Manual
    
    EXECUTING_TOOL --> LOGGED_SUCCESS : Berhasil Ditulis ke Database
    EXECUTING_TOOL --> FAILED_ERROR : Kegagalan Sistem / Rollback
    
    LOGGED_SUCCESS --> [*]
    NOTIFIED_USER --> [*]
    FAILED_ERROR --> [*]
```

---

## 4. Matriks Kolaborasi Antar Agen (Multi-Agent Swarm Flow)

```mermaid
flowchart LR
    subgraph IN["Input"]
        InputMsg["User Message"]
    end

    subgraph ROUTE["Routing"]
        Router["Router Agent"]
    end

    subgraph EXEC["Specialist Agents"]
        direction TB
        Sales["Sales Agent"]
        Inv["Inventory Agent"]
        Fin["Finance Agent"]
        CS["CS Agent"]
    end

    subgraph COOP["Cross-Agent Collaboration"]
        Inv -.->|Info Stok & Spesifikasi| Sales
        Sales -.->|Data Prospek & Nilai Sewa| Fin
        Fin -.->|Status Invoice & Tagihan| CS
    end

    subgraph OUT["Finalization"]
        ResponseBuilder["Response Formatter"]
    end

    InputMsg --> Router
    Router --> Sales
    Router --> Inv
    Router --> Fin
    Router --> CS
    
    Sales --> ResponseBuilder
    Inv --> ResponseBuilder
    Fin --> ResponseBuilder
    CS --> ResponseBuilder
```
