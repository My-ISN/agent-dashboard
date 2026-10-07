# ARSITEKTUR DATABASE & ERD (DATABASE SCHEMA & ERD)
## Deliverable Day 6 — Data Architecture & Entity Relationship Diagram ISKOM

Dokumen ini mendefinisikan arsitektur basis data, rancangan skema 16 entitas inti, dan relasi antar tabel (*Entity Relationship Diagram*) untuk mendukung operasional sistem multi-agent ISKOM AI-OS.

---

## 1. Arsitektur Basis Data (Dual-Layer Data Architecture)

Sistem menggunakan pendekatan **Dual-Layer Database**:
1. **Business & Transactional Layer (HRIS MySQL Database)**:
   - Menyimpan data operasional bisnis riil: Pelanggan, Aset Laptop, Kontrak Sewa, Quotation, Invoice, dan Pembayaran yang terintegrasi dengan ERP HRIS.
2. **AI-OS Governance & State Layer (Dedicated AI Core Database)**:
   - Menyimpan status internal agen: Konfigurasi Agen, Workflow State, Antrean Approval Human-in-the-Loop, Knowledge Base, dan Activity Audit Logs.

---

## 2. Diagram Hubungan Entitas (Entity Relationship Diagram - Mermaid)

```mermaid
erDiagram
    USERS ||--o{ APPROVALS : "decides"
    USERS ||--o{ ACTIVITY_LOGS : "acts"
    AGENTS ||--o{ APPROVALS : "requests"
    AGENTS ||--o{ ACTIVITY_LOGS : "generates"
    AGENTS ||--o{ WORKFLOWS : "executes"
    
    CUSTOMERS ||--o{ LEADS : "submits"
    CUSTOMERS ||--o{ RENTALS : "contracts"
    CUSTOMERS ||--o{ QUOTATIONS : "receives"
    CUSTOMERS ||--o{ INVOICES : "billed"
    CUSTOMERS ||--o{ TICKETS : "files"
    
    LEADS ||--o{ FOLLOW_UPS : "has"
    LEADS ||--o{ QUOTATIONS : "converts_to"
    
    PRODUCTS ||--o{ INVENTORY : "stocked_as"
    QUOTATIONS ||--o{ RENTALS : "formalized_as"
    
    RENTALS ||--o{ INVENTORY : "allocates"
    RENTALS ||--o{ INVOICES : "generates"
    RENTALS ||--o{ TICKETS : "references"
    
    INVOICES ||--o{ PAYMENTS : "settled_by"
    
    WORKFLOWS ||--o{ ACTIVITY_LOGS : "tracked_in"
    KNOWLEDGE ||--o{ AGENTS : "consulted_by"

    USERS {
        int user_id PK
        string name
        string email
        string role
        string status
    }

    AGENTS {
        string agent_id PK
        string name
        string role_title
        string model_name
        json capabilities
        string status
    }

    CUSTOMERS {
        int customer_id PK
        string name
        string phone
        string email
        string customer_type
        string identity_number
        string status
    }

    LEADS {
        int lead_id PK
        int customer_id FK
        string source
        string requirement_summary
        int requested_units
        string pipeline_stage
        datetime created_at
    }

    PRODUCTS {
        int product_id PK
        string sku
        string brand
        string model_name
        string specs_cpu_ram_storage
        decimal base_daily_rate
        decimal base_monthly_rate
    }

    INVENTORY {
        int item_id PK
        int product_id FK
        string serial_number
        string asset_tag
        string condition_status
        string current_location
    }

    QUOTATIONS {
        int quotation_id PK
        string quotation_number
        int lead_id FK
        int customer_id FK
        decimal subtotal_amount
        decimal discount_percent
        decimal final_amount
        string approval_status
    }

    RENTALS {
        int rental_id PK
        string rental_code
        int quotation_id FK
        int customer_id FK
        date start_date
        date end_date
        decimal deposit_amount
        string rental_status
    }

    INVOICES {
        int invoice_id PK
        string invoice_number
        int rental_id FK
        int customer_id FK
        decimal total_due
        date due_date
        string payment_status
    }

    PAYMENTS {
        int payment_id PK
        int invoice_id FK
        decimal amount_paid
        string payment_method
        string bank_reference
        string verification_status
    }

    FOLLOW_UPS {
        int follow_up_id PK
        int lead_id FK
        string agent_id FK
        string channel
        string message_content
        datetime scheduled_at
        string status
    }

    TICKETS {
        int ticket_id PK
        string ticket_number
        int customer_id FK
        int rental_id FK
        string issue_category
        string priority
        string status
    }

    WORKFLOWS {
        int workflow_id PK
        string workflow_name
        string entity_type
        int entity_id
        string current_step
        string execution_state
    }

    APPROVALS {
        int approval_id PK
        string ticket_code
        string requester_agent_id FK
        string trigger_rule_id
        json payload_details
        string status
        int decided_by_user_id FK
        datetime decided_at
    }

    KNOWLEDGE {
        int doc_id PK
        string doc_code
        string title
        string category
        text content_markdown
        string version
        datetime updated_at
    }

    ACTIVITY_LOGS {
        bigint log_id PK
        string transaction_uuid
        datetime timestamp
        string agent_id FK
        int user_id FK
        string action_name
        string tool_called
        json input_params
        json output_result
        int latency_ms
        string status
    }
```

---

## 3. Rincian Kamus Data (16 Entitas Wajib)

### 3.1 Entitas Pengguna & Agen
1. **`users`**: Data pengguna sistem (Owner, Direksi, Sales Staf, Teknisi).
   - Kolom: `user_id` (PK), `name`, `email`, `password_hash`, `role` (`OWNER`, `MANAGER`, `STAFF`), `phone`, `status`, `created_at`.
2. **`agents`**: Registrasi identitas agen AI.
   - Kolom: `agent_id` (PK, misal `AGENT-SLS-01`), `name`, `role_title`, `model_name` (`hermes-3`), `temperature`, `capabilities` (JSON), `status` (`ACTIVE`, `PAUSED`).

### 3.2 Entitas Prospek & Pelanggan
3. **`customers`**: Data profil penyewa laptop (Perorangan / Perusahaan B2B).
   - Kolom: `customer_id` (PK), `name`, `phone`, `email`, `customer_type` (`INDIVIDUAL`, `CORPORATE`), `identity_number` (KTP/NPWP), `address`, `status`.
4. **`leads`**: Pipeline prospek awal dari form web / chat WA.
   - Kolom: `lead_id` (PK), `customer_id` (FK), `source` (`WEB_FORM`, `WHATSAPP`, `ADS`), `requirement_summary`, `requested_units`, `pipeline_stage` (`NEW`, `QUALIFIED`, `NEGOTIATION`, `WON`, `LOST`), `created_at`.
5. **`follow_ups`**: Riwayat dan jadwal sentuhan otomatis kepada prospek.
   - Kolom: `follow_up_id` (PK), `lead_id` (FK), `agent_id` (FK), `channel` (`WHATSAPP`, `EMAIL`), `message_content`, `scheduled_at`, `status` (`PENDING`, `SENT`, `FAILED`).

### 3.3 Entitas Produk, Aset & Inventaris
6. **`products`**: Katalog tipe & spesifikasi laptop/IT.
   - Kolom: `product_id` (PK), `sku`, `brand`, `model_name`, `specs_cpu_ram_storage`, `base_daily_rate`, `base_monthly_rate`, `min_deposit_idr`.
7. **`inventory`**: Data unit fisik individual (berdasarkan Serial Number).
   - Kolom: `item_id` (PK), `product_id` (FK), `serial_number`, `asset_tag`, `condition_status` (`READY_IN_WAREHOUSE`, `BOOKED`, `RENTED`, `MAINTENANCE`, `RETIRED`), `current_location`, `last_qc_date`.

### 3.4 Entitas Transaksi Sewa & Penawaran
8. **`quotations`**: Draf dan dokumen resmi penawaran harga sewa.
   - Kolom: `quotation_id` (PK), `quotation_number`, `lead_id` (FK), `customer_id` (FK), `subtotal_amount`, `discount_percent`, `discount_amount`, `final_amount`, `approval_id` (FK), `approval_status` (`DRAFT`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`).
9. **`rentals`**: Surat Perjanjian / Kontrak Sewa aktif.
   - Kolom: `rental_id` (PK), `rental_code`, `quotation_id` (FK), `customer_id` (FK), `start_date`, `end_date`, `duration_days`, `deposit_amount`, `rental_status` (`ACTIVE`, `EXTENDED`, `COMPLETED`, `OVERDUE`).

### 3.5 Entitas Keuangan & Tagihan
10. **`invoices`**: Lembar tagihan biaya sewa & deposit.
    - Kolom: `invoice_id` (PK), `invoice_number`, `rental_id` (FK), `customer_id` (FK), `subtotal`, `tax_ppn`, `total_due`, `due_date`, `payment_status` (`UNPAID`, `PARTIAL`, `PAID`, `OVERDUE`).
11. **`payments`**: Catatan pembayaran dan mutasi kas bank.
    - Kolom: `payment_id` (PK), `invoice_id` (FK), `amount_paid`, `payment_method` (`BANK_TRANSFER`, `CASH`, `PAYMENT_GATEWAY`), `bank_reference`, `proof_file_path`, `verification_status` (`PENDING`, `VERIFIED`, `REJECTED`).

### 3.6 Entitas Layanan & Bantuan
12. **`tickets`**: Keluhan teknis unit laptop selama masa sewa.
    - Kolom: `ticket_id` (PK), `ticket_number`, `customer_id` (FK), `rental_id` (FK), `item_id` (FK), `issue_category` (`HARDWARE`, `SOFTWARE`, `BATTERY`, `ACCESSORY`), `priority` (`LOW`, `MEDIUM`, `HIGH`, `URGENT`), `status` (`OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`).

### 3.7 Entitas Engine AI & Pengawasan (AI Governance)
13. **`workflows`**: Mesin pelacak tahapan proses otonom.
    - Kolom: `workflow_id` (PK), `workflow_name`, `entity_type` (`LEAD`, `RENTAL`, `TICKET`), `entity_id`, `current_step`, `execution_state` (`RUNNING`, `WAITING_APPROVAL`, `COMPLETED`, `FAILED`), `updated_at`.
14. **`approvals`**: Antrean persetujuan transaksi berisiko tinggi oleh Owner.
    - Kolom: `approval_id` (PK), `ticket_code`, `requester_agent_id` (FK), `trigger_rule_id`, `category` (`DISCOUNT`, `REFUND`, `HIGH_VALUE`), `payload_details` (JSON), `status` (`PENDING`, `APPROVED`, `REJECTED`, `EXPIRED`), `decided_by_user_id` (FK), `decision_notes`, `created_at`, `decided_at`.
15. **`knowledge`**: Repositori SOP, kebijakan harga, dan aturan sewa.
    - Kolom: `doc_id` (PK), `doc_code`, `title`, `category` (`SOP`, `FAQ`, `POLICY`, `PRICING`), `content_markdown`, `version`, `is_active`, `updated_at`.
16. **`activity_logs`**: Audit trail komprehensif setiap detik aktivitas AI.
    - Kolom: `log_id` (PK, BigInt), `transaction_uuid`, `timestamp`, `agent_id` (FK), `user_id` (FK), `action_name`, `tool_called`, `input_params` (JSON), `output_result` (JSON), `error_message`, `latency_ms`, `tokens_used`, `status` (`SUCCESS`, `BLOCKED_BY_RULE`, `FAILED`).
