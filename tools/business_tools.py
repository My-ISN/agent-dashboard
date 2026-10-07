"""
ISKOM AI-OS Business Tools Implementation
8 Fungsi/Alat Utama Operasional Bisnis Rental Laptop.
Semua interaksi database & API dibungkus melalui tools ini.
"""

import uuid
import datetime
from typing import Dict, Any, List, Optional
from tools.registry import ToolRegistry

# Inisialisasi Registry Global
registry = ToolRegistry()

# Simulasi Penyimpanan Data Operasional (In-Memory State Mock)
DB_CUSTOMERS = [
    {"customer_id": "CUST-001", "name": "Budi Santoso", "phone": "081234567890", "type": "INDIVIDUAL", "identity": "3171012345670001"},
    {"customer_id": "CUST-002", "name": "PT Sinergi Digital", "phone": "081987654321", "type": "CORPORATE", "identity": "NPWP-01.234.567.8-012.000"}
]

DB_INVENTORY = {
    "ThinkPad T480": {"ready": 25, "rented": 15, "maintenance": 5, "min_buffer": 2},
    "ThinkPad T490": {"ready": 18, "rented": 10, "maintenance": 2, "min_buffer": 2},
    "Latitude 5400": {"ready": 20, "rented": 5, "maintenance": 0, "min_buffer": 2},
    "MacBook Pro M1": {"ready": 8, "rented": 3, "maintenance": 1, "min_buffer": 1}
}

DB_QUOTATIONS = []
DB_LEADS = []
DB_TICKETS = []
DB_APPROVAL_REQUESTS = []
DB_OUTBOX_MESSAGES = []


# =============================================================================
# 1. search_customer()
# =============================================================================
@registry.register(
    name="search_customer",
    description="Mencari data profil dan riwayat pelanggan berdasarkan nomor telepon atau nama",
    allowed_agents=["AGENT-SLS-01", "AGENT-CS-01", "AGENT-FIN-01", "AGENT-MGR-01"]
)
def search_customer(query: str) -> Dict[str, Any]:
    q = query.lower()
    for cust in DB_CUSTOMERS:
        if q in cust["phone"] or q in cust["name"].lower():
            return {"found": True, "customer": cust}
    return {"found": False, "message": f"Pelanggan dengan kata kunci '{query}' belum terdaftar."}


# =============================================================================
# 2. search_product()
# =============================================================================
@registry.register(
    name="search_product",
    description="Mencari spesifikasi produk laptop dan tarif sewa dari katalog resmi",
    allowed_agents=["AGENT-SLS-01", "AGENT-CS-01", "AGENT-MGR-01"]
)
def search_product(query: str) -> Dict[str, Any]:
    q = query.lower()
    for model, stock in DB_INVENTORY.items():
        if q in model.lower():
            return {
                "model": model,
                "status": "AVAILABLE" if stock["ready"] > stock["min_buffer"] else "LOW_STOCK",
                "ready_stock": stock["ready"]
            }
    return {"model": query, "status": "NOT_FOUND", "ready_stock": 0}


# =============================================================================
# 3. check_inventory()
# =============================================================================
@registry.register(
    name="check_inventory",
    description="Mengecek stok fisik laptop di gudang dan memvalidasi batas safety buffer",
    allowed_agents=["AGENT-INV-01", "AGENT-SLS-01", "AGENT-OPS-01", "AGENT-MGR-01"]
)
def check_inventory(model_or_sku: str, requested_qty: int) -> Dict[str, Any]:
    matched_model = None
    for model in DB_INVENTORY:
        if model_or_sku.lower() in model.lower():
            matched_model = model
            break

    if not matched_model:
        return {
            "model": model_or_sku,
            "is_available": False,
            "reason": "Model tidak ditemukan di inventaris",
            "ready_stock": 0
        }

    inv = DB_INVENTORY[matched_model]
    available_to_rent = max(0, inv["ready"] - inv["min_buffer"])
    is_available = requested_qty <= available_to_rent

    return {
        "model": matched_model,
        "requested_qty": requested_qty,
        "ready_stock_total": inv["ready"],
        "available_to_rent": available_to_rent,
        "safety_buffer_reserved": inv["min_buffer"],
        "is_available": is_available,
        "message": "Stok memadai untuk diproses" if is_available else f"Stok tidak mencukupi (Tersedia aman: {available_to_rent} unit)"
    }


# =============================================================================
# 4. create_lead()
# =============================================================================
@registry.register(
    name="create_lead",
    description="Mendaftarkan calon penyewa baru ke dalam CRM pipeline",
    allowed_agents=["AGENT-SLS-01", "AGENT-CS-01", "AGENT-MGR-01"]
)
def create_lead(customer_name: str, phone: str, requirement: str, qty: int = 1) -> Dict[str, Any]:
    lead_id = f"LEAD-{uuid.uuid4().hex[:6].upper()}"
    new_lead = {
        "lead_id": lead_id,
        "customer_name": customer_name,
        "phone": phone,
        "requirement": requirement,
        "qty": qty,
        "stage": "NEW",
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    DB_LEADS.append(new_lead)
    return {"lead_id": lead_id, "status": "CREATED", "stage": "NEW"}


# =============================================================================
# 5. create_quotation()
# =============================================================================
@registry.register(
    name="create_quotation",
    description="Menerbitkan draf surat penawaran harga sewa resmi dengan validasi diskon",
    allowed_agents=["AGENT-SLS-01", "AGENT-MGR-01"],
    requires_approval=False  # Kecuali diskon > 10%
)
def create_quotation(customer_name: str, unit_model: str, qty: int, duration_months: int, discount_percent: float = 0.0) -> Dict[str, Any]:
    rate_monthly = 950000
    if "i7" in unit_model.lower() or "t490" in unit_model.lower():
        rate_monthly = 1350000
    elif "macbook" in unit_model.lower():
        rate_monthly = 2800000

    subtotal = rate_monthly * qty * duration_months
    discount_amount = int(subtotal * (discount_percent / 100.0))
    final_amount = subtotal - discount_amount

    quo_id = f"QUO/ISKOM/2026/{uuid.uuid4().hex[:6].upper()}"
    quotation = {
        "quotation_id": quo_id,
        "customer_name": customer_name,
        "unit_model": unit_model,
        "qty": qty,
        "duration_months": duration_months,
        "subtotal": subtotal,
        "discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    DB_QUOTATIONS.append(quotation)

    return {
        "quotation_id": quo_id,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "status": "ISSUED"
    }


# =============================================================================
# 6. send_message()
# =============================================================================
@registry.register(
    name="send_message",
    description="Mengirimkan pesan notifikasi atau konfirmasi via WhatsApp atau Web UI",
    allowed_agents=["AGENT-SLS-01", "AGENT-CS-01", "AGENT-FIN-01", "AGENT-OPS-01", "AGENT-MGR-01"]
)
def send_message(channel: str, recipient: str, message_text: str) -> Dict[str, Any]:
    msg_id = f"MSG-{uuid.uuid4().hex[:8].upper()}"
    outbox_entry = {
        "msg_id": msg_id,
        "channel": channel,
        "recipient": recipient,
        "text": message_text,
        "sent_at": datetime.datetime.utcnow().isoformat(),
        "status": "SENT"
    }
    DB_OUTBOX_MESSAGES.append(outbox_entry)
    return {"msg_id": msg_id, "channel": channel, "status": "DELIVERED"}


# =============================================================================
# 7. create_ticket()
# =============================================================================
@registry.register(
    name="create_ticket",
    description="Membuka tiket kendala teknis atau komplain pelanggan di sistem Helpdesk",
    allowed_agents=["AGENT-CS-01", "AGENT-OPS-01", "AGENT-MGR-01"]
)
def create_ticket(customer_name: str, issue_category: str, description: str, priority: str = "MEDIUM") -> Dict[str, Any]:
    tck_id = f"TCK-{uuid.uuid4().hex[:6].upper()}"
    ticket = {
        "ticket_id": tck_id,
        "customer_name": customer_name,
        "category": issue_category,
        "description": description,
        "priority": priority,
        "status": "OPEN",
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    DB_TICKETS.append(ticket)
    return {"ticket_id": tck_id, "priority": priority, "status": "OPEN"}


# =============================================================================
# 8. request_approval()
# =============================================================================
@registry.register(
    name="request_approval",
    description="Mengirimkan pengajuan persetujuan transaksi/diskon ke antrean Owner",
    allowed_agents=["AGENT-SLS-01", "AGENT-FIN-01", "AGENT-INV-01", "AGENT-MGR-01"]
)
def request_approval(requester_agent_id: str, rule_id: str, category: str, payload: dict, rationale: str) -> Dict[str, Any]:
    apv_id = f"APV-{uuid.uuid4().hex[:6].upper()}"
    req = {
        "approval_id": apv_id,
        "requester_agent": requester_agent_id,
        "rule_id": rule_id,
        "category": category,
        "payload": payload,
        "rationale": rationale,
        "status": "PENDING_OWNER",
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    DB_APPROVAL_REQUESTS.append(req)
    return {
        "approval_id": apv_id,
        "status": "PENDING_OWNER",
        "message": "Pengajuan berhasil dikirimkan ke antrean approval Owner"
    }
