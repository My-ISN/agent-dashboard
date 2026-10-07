"""
ISKOM AI-OS Semantic Intent Router
Orchestrating prompt categorization and routing to specialist agents.
"""

import re
import os
import json
from typing import Dict, Any, Tuple
from core.models import UserMessage, RouteDecision


class IntentRouter:
    """Router semantik untuk mengklasifikasi instruksi pengguna ke agen yang tepat"""

    def __init__(self):
        # Pemetaan Agen Resmi ISKOM
        self.agent_registry = {
            "AGENT-SLS-01": "Sales & Rental Agent",
            "AGENT-INV-01": "Inventory & Unit Agent",
            "AGENT-FIN-01": "Finance & Invoicing Agent",
            "AGENT-CS-01": "Customer Service & Support Agent",
            "AGENT-KPI-01": "KPI & Executive Agent",
        }

    def route(self, message: UserMessage) -> RouteDecision:
        """Menganalisis teks pesan dan mengembalikan keputusan routing (RouteDecision)"""
        text = message.text.strip().lower()

        # Ekstraksi Entitas Umum (Quantity, Unit Model, Diskon, Invoice No)
        entities = self._extract_entities(message.text)

        # 1. Deteksi Evaluasi KPI / Eksekutif / Laporan Omset
        if any(k in text for k in ["omset", "kpi", "utilisasi", "laporan eksekutif", "rekap bisnis", "ringkasan pendapatan"]):
            return RouteDecision(
                agent_id="AGENT-KPI-01",
                agent_name=self.agent_registry["AGENT-KPI-01"],
                intent="EXECUTIVE_KPI_QUERY",
                confidence=0.96,
                extracted_entities=entities,
                reasoning="Instruksi meminta rekap metrik kinerja bisnis atau omset sewa untuk level manajemen."
            )

        # 2. Deteksi Finance / Invoicing / Tagihan / Pembayaran
        if any(k in text for k in ["invoice", "tagihan", "pembayaran", "bukti transfer", "rekening", "lunas", "refund", "deposit uang"]):
            return RouteDecision(
                agent_id="AGENT-FIN-01",
                agent_name=self.agent_registry["AGENT-FIN-01"],
                intent="FINANCE_BILLING_QUERY",
                confidence=0.95,
                extracted_entities=entities,
                reasoning="Instruksi berkaitan dengan penagihan invoice, status pembayaran, atau urusan finansial sewa."
            )

        # 3. Deteksi Kendala Teknis / Komplain / Customer Service / Rusak
        if any(k in text for k in ["rusak", "mati", "error", "bergaris", "flickering", "komplain", "kendala", "bantuan teknis", "charger rusak", "baterai drop"]):
            return RouteDecision(
                agent_id="AGENT-CS-01",
                agent_name=self.agent_registry["AGENT-CS-01"],
                intent="TECHNICAL_SUPPORT_COMPLAINT",
                confidence=0.98,
                extracted_entities=entities,
                reasoning="Instruksi melaporkan masalah fisik atau keluhan operasional unit laptop sewa."
            )

        # 4. Deteksi Inventory / Cek Stok Fisik Gudang
        if any(k in text for k in ["cek stok", "ketersediaan", "ready gak", "ready tidak", "ada stok", "stok fisik", "gudang", "masih ada berapa"]):
            return RouteDecision(
                agent_id="AGENT-INV-01",
                agent_name=self.agent_registry["AGENT-INV-01"],
                intent="INVENTORY_STOCK_CHECK",
                confidence=0.94,
                extracted_entities=entities,
                reasoning="Instruksi menanyakan ketersediaan fisik stok laptop di gudang."
            )

        # 5. Default / Rental & Sales (Sewa, Quotation, Permintaan Unit, Diskon)
        return RouteDecision(
            agent_id="AGENT-SLS-01",
            agent_name=self.agent_registry["AGENT-SLS-01"],
            intent="RENTAL_SALES_INQUIRY",
            confidence=0.92,
            extracted_entities=entities,
            reasoning="Instruksi berkaitan dengan kebutuhan penyewaan unit laptop, penawaran harga, atau negosiasi sewa."
        )

    def _extract_entities(self, raw_text: str) -> Dict[str, Any]:
        """Ekstraksi entitas kunci seperti kuantitas, jenis unit, diskon, dan invoice"""
        entities = {}
        text = raw_text.lower()

        # Ekstraksi Kuantitas (misal: "50 laptop", "10 unit", "20 pc")
        qty_match = re.search(r'(\d+)\s*(?:unit|laptop|pc|buah|perangkat)', text)
        if qty_match:
            entities["quantity"] = int(qty_match.group(1))

        # Ekstraksi Diskon (misal: "diskon 15%", "potongan 20 %")
        disc_match = re.search(r'diskon\s*(\d+(?:\.\d+)?)\s*%', text)
        if disc_match:
            entities["discount_percent"] = float(disc_match.group(1))

        # Ekstraksi Model Laptop
        if "thinkpad" in text or "lenovo" in text:
            entities["unit_model"] = "Lenovo ThinkPad"
        elif "macbook" in text:
            entities["unit_model"] = "Apple MacBook"
        elif "dell" in text:
            entities["unit_model"] = "Dell Latitude"
        elif "hp" in text:
            entities["unit_model"] = "HP EliteBook"
        elif "i7" in text:
            entities["unit_model"] = "Laptop Core i7"
        elif "i5" in text:
            entities["unit_model"] = "Laptop Core i5"

        # Ekstraksi Durasi Sewa
        dur_match = re.search(r'(\d+)\s*(?:hari|bulan|minggu|tahun)', text)
        if dur_match:
            entities["duration_raw"] = dur_match.group(0)

        # Ekstraksi Nomor Invoice
        inv_match = re.search(r'(#?inv[-_\d\w]+)', text, re.IGNORECASE)
        if inv_match:
            entities["invoice_number"] = inv_match.group(1).upper()

        return entities
